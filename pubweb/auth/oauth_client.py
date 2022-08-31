import time
from datetime import datetime

import boto3
import jwt
import requests
from requests.auth import AuthBase

from pubweb import config
from pubweb.auth import AuthInfo


def _authenticate():
    params = {'client_id': config.app_id}
    resp = requests.get(f'{config.auth_endpoint}/device-code', params=params)

    flow = resp.json()
    print(flow['message'])

    params = {
        'client_id': config.app_id,
        'device_code': flow['device_code'],
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    }
    auth_status = 'authorization_pending'
    while auth_status == 'authorization_pending':
        time.sleep(flow['interval'])
        resp = requests.get(f'{config.auth_endpoint}/token', params=params)
        token_result = resp.json()
        auth_status = token_result.get('message')

        if 'access_token' in token_result:
            return token_result

    raise RuntimeError(f'error authenticating {auth_status}')


def decode_token(token):
    return jwt.decode(token,
                      options={"verify_signature": False})


class ClientAuth(AuthInfo):
    def __init__(self, cache: bool):
        # TODO: Implement cache
        self.token_info = _authenticate()
        self._update_token_metadata()

    def get_request_auth(self) -> AuthBase:
        return self.RequestAuth(self._get_token()['access_token'])

    def get_current_user(self) -> str:
        return self.username

    def _get_token(self):
        # Check if refresh token is expired, re-auth using device code flow
        if datetime.now() > self.refresh_token_expiry:
            self.token_info = _authenticate()

        # Refresh access token using refresh token
        if datetime.now() > self.access_token_expiry:
            self._refresh_access_token()

        return self.token_info

    def _refresh_access_token(self):
        cognito = boto3.client('cognito-idp', region_name=config.region)
        resp = cognito.iniate_auth(
            ClientId=config.app_id,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': self.token_info['refresh_token']
            }
        )
        auth_result = resp['AuthenticationResult']
        self.token_info['access_token'] = auth_result['AccessToken']
        self.token_info['refresh_token'] = auth_result['RefreshToken']
        self.token_info['id_token'] = auth_result['IdToken']
        self._update_token_metadata()

    def _update_token_metadata(self):
        decoded_access_token = decode_token(self.token_info['access_token'])
        decoded_refresh_token = decode_token(self.token_info['refresh_token'])
        self.access_token_expiry = datetime.fromtimestamp(decoded_access_token['exp'])
        self.refresh_token_expiry = datetime.fromtimestamp(decoded_refresh_token['exp'])
        self.username = decoded_access_token['username']

    class RequestAuth(AuthBase):
        def __init__(self, token):
            self.token = token

        def __call__(self, request):
            request.headers['Authorization'] = self.token
            return request
