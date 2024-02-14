import os
import sys
import time

import boto3

WORKER_CMD = 'celery -A shapeworks_cloud.celery worker -n $HOSTNAME -Q gpu --detach'


def inspect_queue(queue_name):
    from .celery import app

    with app.pool.acquire(block=True) as conn:
        queue = conn.get_manager().get_queue('/', queue_name)
        messages = queue.get('messages_ready', -1)
        return messages


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


def get_gpu_workers(client):
    gpu_workers = []
    for worker in get_all_workers(client):
        print(worker)
        if worker['tags'] is not None and any(
            t['Key'] == 'GPU' and t['Value'] == 'true' for t in worker['tags']
        ):
            gpu_workers.append(worker)

    return gpu_workers


def manage_workers(**kwargs):
    print('Managing GPU workers.')
    for k, v in kwargs.items():
        os.environ[k] = v

    num_queued = inspect_queue('gpu')
    if num_queued < 0:
        return
    print(f'{num_queued} tasks in queue.')

    client = boto3.client('ec2')

    gpu_workers = get_gpu_workers(client)

    if num_queued > 0:
        ids_to_start = [w['id'] for w in gpu_workers if not w['hostname']]
        if len(ids_to_start) > num_queued:
            ids_to_start = ids_to_start[:num_queued]

        if len(ids_to_start) > 0:
            print(f'Starting instances {ids_to_start}.')
            print(client.start_instances(InstanceIds=ids_to_start))
            print('Waiting 10 seconds before sending celery command to instances.')
            time.sleep(10)
            print(f'Sending celery command to {ids_to_start}.')
            print(
                client.send_command(
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': [WORKER_CMD]},
                    InstanceIds=ids_to_start,
                )
            )
        else:
            print('All available GPU workers are live. Tasks in queue must wait.')

    else:
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
    time.sleep(60)

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
