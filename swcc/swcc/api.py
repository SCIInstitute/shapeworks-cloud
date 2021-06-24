from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import requests
from requests_toolbelt.sessions import BaseUrlSession
from s3_file_field_client import S3FileFieldClient
from urllib3.util.retry import Retry

from . import __version__

_session_stack: List[SwccSession] = []


def current_session():
    global _session_stack
    if not _session_stack:
        raise Exception('An active session context is required')

    return _session_stack[-1]


@contextmanager
def swcc_session(**kwargs):
    global _session_stack
    _session_stack.append(SwccSession(**kwargs))
    try:
        yield _session_stack[-1]
    finally:
        s = _session_stack.pop()
        s.close()


class SwccSession(BaseUrlSession):
    def __init__(
        self,
        base_url: str = 'https://app.shapeworks-cloud.org/api/v1',
        token: Optional[str] = None,
        **kwargs,
    ):
        base_url = f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        super().__init__(base_url=base_url, **kwargs)

        self.cache: Dict[Any, Dict[int, Any]] = defaultdict(dict)
        retry = Retry()
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.mount(base_url, adapter)

        self.headers.update(
            {
                'User-agent': f'swcc/{__version__}',
                'Accept': 'application/json',
            }
        )
        self.s3ff = S3FileFieldClient(f'{base_url}s3-upload/', self)
        if token:
            self.set_token(token)

    def set_token(self, token: str):
        self.headers['Authorization'] = f'Token {token}'

    def login(self, username: str, password: str) -> str:
        auth_url = f'{self.base_url.rstrip("/").replace("/api/v1", "")}/api-token-auth/'
        resp = requests.post(auth_url, data={'username': username, 'password': password})
        if resp.status_code != 200:
            raise Exception('Invalid username or password provided')
        token = resp.json()['token']
        self.set_token(token)
        return token
