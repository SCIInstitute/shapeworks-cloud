from typing import Dict, Iterable

import requests
from requests_toolbelt.sessions import BaseUrlSession

from . import __version__


class SwccSession(BaseUrlSession):
    page_size = 50

    def __init__(self, base_url: str, **kwargs):
        base_url = f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        super().__init__(base_url=base_url, **kwargs)

        self.headers.update(
            {
                'User-agent': f'swcc/{__version__}',
                'Accept': 'application/json',
            }
        )

    def set_token(self, token: str):
        self.headers['Authorization'] = f'Token {token}'

    def login(self, username: str, password: str) -> requests.Response:
        auth_url = f'{self.base_url.rstrip("/").replace("/api/v1", "")}/api-token-auth/'
        resp = requests.post(auth_url, data={'username': username, 'password': password})
        if resp.status_code != 200:
            raise Exception('Invalid username or password provided')
        self.set_token(resp.json()['token'])
        return resp

    def all_paginated_results(self, url: str) -> Iterable[Dict]:
        page = 1
        page_size = 20
        iterate = True
        while iterate:
            response = self.get(url, params={'page': page, 'page_size': page_size})
            response.raise_for_status()
            json = response.json()
            iterate = json['next'] is not None
            for result in json['results']:
                yield result
            page += 1
