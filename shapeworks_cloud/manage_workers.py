from pathlib import Path
import re
import subprocess

MAX_WORKERS = 3
BASE_DIR = Path(__file__).parent
WORKER_TAG = 'mock-gpu'
WORKER_DOCKERFILE = 'dev/django.Dockerfile'
WORKER_ENV_FILE = 'dev/.env.celery.docker-compose'
WORKER_ENTRYPOINT = './dev/worker.sh'
WORKER_CMD = 'celery -A shapeworks_cloud.celery worker -n $HOSTNAME -Q gpu'


def manage_workers(**kwargs):
    print(f'Managing workers. Kwargs: {kwargs}')

    num_queued = inspect_queue('gpu')
    print(f'{num_queued} tasks in queue.')

    available_workers = filter_workers(get_containers())
    live_workers = [w for w in available_workers if 'Up ' in w['STATUS']]
    if num_queued > 0:
        ensure_build_ready()
        while len(available_workers) < MAX_WORKERS:
            create_new_worker()
            available_workers = filter_workers(get_containers())
        print(f'{len(available_workers)} available workers.')

        while len(live_workers) < MAX_WORKERS and len(live_workers) < num_queued:
            for w in available_workers:
                if 'Up' not in w['STATUS']:
                    start_worker(w)
                    break
            available_workers = filter_workers(get_containers())
            live_workers = [w for w in available_workers if 'Up ' in w['STATUS']]
    else:
        for worker in live_workers:
            stop_worker(worker)


def inspect_queue(queue_name):
    from .celery import app

    with app.pool.acquire(block=True) as conn:
        queue = conn.get_manager().get_queue('/', queue_name)
        messages = queue.get('messages_ready', 0)
        return messages


def get_containers():
    output = subprocess.Popen(
        ['docker', 'container', 'ls', '-a'],
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    if output:
        lines = output.read().split('\n')
        columns = re.split('[  ]{2,}', lines[0])
        column_starts = [lines[0].find(c) for c in columns]
        column_starts.append(-1)
        container_list = [
            {k: c[column_starts[i] : column_starts[i + 1]].strip() for i, k in enumerate(columns)}
            for c in lines[1:-1]
        ]
        return container_list


def filter_workers(container_list):
    return [c for c in container_list if WORKER_TAG in c['IMAGE']]


def ensure_build_ready():
    output = subprocess.Popen(
        ['docker', 'image', 'ls'],
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    if output:
        image_list = [[j.strip() for j in i.split('\t')] for i in output.read().split('\n')][1:-1]
        target_image_exists = any(WORKER_TAG in i[0] for i in image_list)

        if not target_image_exists:
            subprocess.call(
                ['docker', 'build', '-t', WORKER_TAG, '-f', WORKER_DOCKERFILE, '.'],
                stdout=subprocess.PIPE,
            )


def create_new_worker():
    id = (
        subprocess.check_output(
            [
                'docker',
                'create',
                '--env-file',
                WORKER_ENV_FILE,
                '--network=host',
                '--entrypoint=/bin/bash',
                '-it',
                # '--gpus=all',
                WORKER_TAG,
                '-c',
                WORKER_CMD,
            ]
        )
        .decode()
        .replace('\n', '')
    )
    subprocess.check_output(
        # cannot mount mounted volume, instead must copy data
        # https://forums.docker.com/t/mounting-a-volume-not-working-with-running-docker-in-docker/25775
        [
            'docker',
            'cp',
            '.',
            f'{id}:/opt/django-project',
        ]
    )


def start_worker(worker):
    id = worker.get('CONTAINER ID')
    if not id:
        raise ValueError('Cannot start worker without "CONTAINER ID".')
    print(f'Starting worker {id}.')
    subprocess.call(
        ['docker', 'start', id],
    )


def stop_worker(worker):
    id = worker.get('CONTAINER ID')
    if not id:
        raise ValueError('Cannot stop worker without "CONTAINER ID".')
    print(f'Stopping worker {id}.')
    subprocess.call(
        ['docker', 'stop', id],
    )
