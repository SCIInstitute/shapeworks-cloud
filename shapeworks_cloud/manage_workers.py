import os

import boto3


def manage_workers(**kwargs):
    print('Managing GPU workers.')
    for k, v in kwargs.items():
        os.environ[k] = v

    num_queued = inspect_queue('gpu')
    if num_queued < 0:
        return
    print(f'{num_queued} tasks in queue.')

    client = boto3.client('ec2')

    gpu_workers = []
    reservations = client.describe_instances().get('Reservations', [])
    for reservation in reservations:
        instances = reservation.get('Instances', [])
        for instance in instances:
            tags = instance.get('Tags', [])
            if any(t['Key'] == 'GPU' and t['Value'] == 'true' for t in tags):
                gpu_workers.append(
                    {'id': instance.get('InstanceId'), 'hostname': instance.get('PublicDnsName')}
                )

    if num_queued > 0:
        ids_to_start = [w['id'] for w in gpu_workers if not w['hostname']]
        if len(ids_to_start) > num_queued:
            ids_to_start = ids_to_start[:num_queued]

        if len(ids_to_start) > 0:
            print(f'Starting instances {ids_to_start}.')
            print(client.start_instances(InstanceIds=ids_to_start))
        else:
            print('All available GPU workers are live. Tasks in queue must wait.')

    else:
        ids_to_stop = [w['id'] for w in gpu_workers if w['hostname']]

        if len(ids_to_stop) > 0:
            print(f'Stopping instances {ids_to_stop}.')
            print(client.stop_instances(InstanceIds=ids_to_stop))

    client.close()


def inspect_queue(queue_name):
    from .celery import app

    with app.pool.acquire(block=True) as conn:
        queue = conn.get_manager().get_queue('/', queue_name)
        messages = queue.get('messages_ready', -1)
        return messages
