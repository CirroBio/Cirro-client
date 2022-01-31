import requests
from requests.auth import AuthBase

from pubweb import config

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


class RestClient:
    def __init__(self, auth_info: AuthBase):
        self.endpoint = config.rest_endpoint
        self.auth_info = auth_info

    def post(self, path, data=None):
        url = f'{self.endpoint}/{path}'
        return requests.post(url, json=data, headers=HEADERS, auth=self.auth_info)

    def get(self, path, query_params=None):
        url = f'{self.endpoint}/{path}'
        return requests.get(url, params=query_params, headers=HEADERS, auth=self.auth_info)

