import datetime
import os
from pathlib import Path
import sys
import time

import boto3

# DEPLOY_LOCK = Path('/opt/django-project/dev/deploy.lock')  # for development
DEPLOY_LOCK = Path('/home/ubuntu/celery_project/dev/deploy.lock')
MAX_LOCK_TIME = datetime.timedelta(minutes=10)


def inspect_queue(queue_name):
    import pyrabbit

    from .celery import app

    # this function requires pyrabbit and the rabbitmq management port
    num_messages_ready = -1
    num_messages_active = -1
    with app.pool.acquire(block=True) as conn:
        try:
            manager = conn.get_manager()
            vhost = '/'
            configuration = os.environ.get('DJANGO_CONFIGURATION')
            if configuration == 'HerokuProductionConfiguration':
                # Override manager hostname and vhost in production;
                # CloudAMQP management not served through dedicated port and must use https
                # and vhost is assigned name of user (instead of using default '/')
                manager.http.base_url = manager.http.base_url.replace(':15672', '').replace(
                    'http', 'https'
                )
                vhost = manager.user
            queue = manager.get_queue(vhost, queue_name)
            num_messages = queue.get('messages', -1)
            num_messages_ready = queue.get('messages_ready', -1)
            if num_messages >= 0:
                num_messages_active = num_messages - num_messages_ready
        except pyrabbit.http.HTTPError:
            # queue doesn't exist yet, wait for a spawned task to create it
            pass
    return num_messages_ready, num_messages_active


def get_all_workers(client):
    workers = []
    reservations = client.describe_instances().get('Reservations', [])
    for reservation in reservations:
        instances = reservation.get('Instances', [])
        for instance in instances:
            name = None
            tags = instance.get('Tags', [])
            for tag in tags:
                if tag.get('Key') == 'Name':
                    name = tag.get('Value')
            if name is not None:
                workers.append(
                    {
                        'id': instance.get('InstanceId'),
                        'name': name,
                        'hostname': instance.get('PublicDnsName'),
                        'tags': tags,
                    }
                )
    return workers


# Filtering for GPU-enabled workers
# This implementation assumes GPU-enabled instances have
# A tag with the key "GPU" and the value "true"
def get_gpu_workers(client):
    gpu_workers = []
    for worker in get_all_workers(client):
        if worker['tags'] is not None and any(
            t['Key'] == 'GPU' and t['Value'] == 'true' for t in worker['tags']
        ):
            gpu_workers.append(worker)

    return gpu_workers


def manage_workers(**kwargs):
    print('Managing GPU workers.')
    for k, v in kwargs.items():
        if v is not None:
            os.environ[k] = v

    # check for lockfile indicating that a deployment is active
    if DEPLOY_LOCK.exists():
        with open(DEPLOY_LOCK) as lock:
            lock_content = lock.readlines()
            if len(lock_content) > 0:
                lock_time = datetime.datetime.strptime(
                    lock_content[0].replace('\n', ''), '%Y.%m.%d-%H.%M.%S'
                )
                time_delta = datetime.datetime.now() - lock_time
                max_mins = MAX_LOCK_TIME.total_seconds() / 60
                explanation = f"Deploy playbook started %s {max_mins} mins ago and hasn't exited."
                if time_delta < MAX_LOCK_TIME:
                    result = 'Valid deployment lockfile found. Skipping worker management.'
                    print(f"{result} {explanation % 'less than'}")
                    return
                else:
                    result = 'Invalid deployment lockfile found. Continuing with worker management.'
                    print(f"{result} {explanation % 'greater than'}")

    num_messages_ready, num_messages_active = inspect_queue('gpu')
    if num_messages_ready < 0:
        return
    print(f'{num_messages_ready} tasks ready, {num_messages_active} tasks active.')

    client = boto3.client('ec2')
    gpu_workers = get_gpu_workers(client)

    if num_messages_ready > 0:
        ids_to_start = [w['id'] for w in gpu_workers if not w['hostname']]
        if len(ids_to_start) > num_messages_ready:
            ids_to_start = ids_to_start[:num_messages_ready]

        if len(ids_to_start) > 0:
            print(f'Starting instances {ids_to_start}.')
            print(client.start_instances(InstanceIds=ids_to_start))
        else:
            print('All available GPU workers are live. Tasks in queue must wait.')

    elif num_messages_active == 0:
        ids_to_stop = [w['id'] for w in gpu_workers if w['hostname']]

        if len(ids_to_stop) > 0:
            print(f'Stopping instances {ids_to_stop}.')
            print(client.stop_instances(InstanceIds=ids_to_stop))

    client.close()


def start_all():
    client = boto3.client('ec2')
    all_workers = get_all_workers(client)
    all_ids = [w['id'] for w in all_workers]
    client.start_instances(InstanceIds=all_ids)

    # Wait for startup
    time.sleep(30)

    # Refresh hostnames
    all_workers = get_all_workers(client)

    # Print hostnames to console for ansible inventory
    print(','.join([w['hostname'] for w in all_workers]) + ',')

    client.close()


def stop_gpus():
    client = boto3.client('ec2')
    gpu_workers = get_gpu_workers(client)
    all_ids = [w['id'] for w in gpu_workers]
    client.stop_instances(InstanceIds=all_ids)
    client.close()


if __name__ == '__main__':
    if sys.argv[1] == 'start_all':
        start_all()
    elif sys.argv[1] == 'stop_gpus':
        stop_gpus()
