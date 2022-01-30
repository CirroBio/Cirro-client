import requests
from requests.auth import AuthBase

from pubweb import config


class RestClient:
    def __init__(self, auth_info: AuthBase):
        self.endpoint = config.rest_endpoint
        self.auth_info = auth_info

    def post(self, path, data=None):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        url = f'{self.endpoint}/{path}'
        return requests.post(url, json=data, headers=headers, auth=self.auth_info)
