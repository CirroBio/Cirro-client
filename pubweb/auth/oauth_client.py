import json
import logging
import time
from datetime import datetime
from pathlib import Path

import boto3
import jwt
import requests
from msal_extensions import build_encrypted_persistence, FilePersistence
from requests.auth import AuthBase

from pubweb import config
from pubweb.auth import AuthInfo
from pubweb.models.auth import DeviceTokenResponse, OAuthTokenResponse

logger = logging.getLogger()
TOKEN_PATH = Path('~', '.pubweb', '.token.dat').expanduser()


def _build_token_persistence(location, fallback_to_plaintext=False):
    try:
        return build_encrypted_persistence(location)
    except:  # pylint: disable=bare-except
        if not fallback_to_plaintext:
            raise
        logger.warning("Encryption unavailable. Opting in to plain text.")
        return FilePersistence(location)


def _authenticate():
    params = {'client_id': config.app_id}
    resp = requests.get(f'{config.auth_endpoint}/device-code', params=params)

    flow: DeviceTokenResponse = resp.json()
    print(flow['message'])
    device_expiry = datetime.fromisoformat(flow['expiry'])

    params = {
        'client_id': config.app_id,
        'device_code': flow['device_code'],
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    }
    auth_status = 'authorization_pending'
    while auth_status == 'authorization_pending':
        time.sleep(flow['interval'])
        if device_expiry < datetime.now():
            raise RuntimeError(f'Timed out')

        resp = requests.get(f'{config.auth_endpoint}/token', params=params)
        token_result: OAuthTokenResponse = resp.json()
        auth_status = token_result.get('message')

        if 'access_token' in token_result:
            return token_result

    raise RuntimeError(f'error authenticating {auth_status}')


def decode_token(token):
    return jwt.decode(token, options={"verify_signature": False})


class ClientAuth(AuthInfo):
    def __init__(self, enable_cache: bool):
        if enable_cache:
            persistence = _build_token_persistence(TOKEN_PATH, fallback_to_plaintext=False)
            self.token_info = json.loads(persistence.load())

            if not self.token_info:
                self.token_info = _authenticate()
                persistence.save(json.dumps(self.token_info))

        else:
            self.token_info = _authenticate()

        self._update_token_metadata()

    def get_request_auth(self) -> AuthBase:
        return self.RequestAuth(self._get_token()['access_token'])

    def get_current_user(self) -> str:
        return self.username

    def _get_token(self):
        # Check if refresh token is expired, re-auth using device code flow
        if self.refresh_token_expiry < datetime.now():
            self.token_info = _authenticate()

        # Refresh access token using refresh token
        if self.access_token_expiry < datetime.now():
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
