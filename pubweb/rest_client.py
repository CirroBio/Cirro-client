import requests
from requests.auth import AuthBase

PUB_WEB_ENDPOINT = 'https://2yi247yljl.execute-api.us-west-2.amazonaws.com/prd'


class RestClient:
    def __init__(self, auth_info: AuthBase, endpoint=PUB_WEB_ENDPOINT):
        self.endpoint = endpoint
        self.auth_info = auth_info

    def post(self, path, data=None):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        url = f'{self.endpoint}/{path}'
        return requests.post(url, json=data, headers=headers, auth=self.auth_info)
