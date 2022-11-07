import logging
from datetime import datetime, timedelta
from typing import Callable

import boto3
from pycognito import AWSSRP
from requests.auth import AuthBase

from pubweb.api.auth.base import AuthInfo
from pubweb.api.config import config

logger = logging.getLogger()


class UsernameAndPasswordAuth(AuthInfo):
    """
    Uses your username & password to authenticate
    Note: this does not work with federated identities (Fred Hutch login)
    You must contact HDC to manually create an account
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth_result = None
        self.token_expiry = None

    def get_request_auth(self) -> AuthBase:
        return self.RequestAuth(lambda: self._get_token()['AccessToken'])

    def get_current_user(self) -> str:
        return self.username

    def _get_token(self):
        if self.token_expiry and self.token_expiry > datetime.now():
            return self.auth_result

        logger.debug('Fetching new token from cognito')
        cognito = boto3.client('cognito-idp', region_name=config.region)
        aws = AWSSRP(username=self.username,
                     password=self.password,
                     pool_id=config.user_pool_id,
                     client_id=config.app_id,
                     client=cognito)
        resp = aws.authenticate_user()
        self.auth_result = resp['AuthenticationResult']
        self.token_expiry = datetime.now() + timedelta(seconds=self.auth_result['ExpiresIn'])
        return self.auth_result

    class RequestAuth(AuthBase):
        def __init__(self, token_getter: Callable[..., str]):
            self.token_getter = token_getter

        def __call__(self, request):
            request.headers['Authorization'] = self.token_getter()
            return request
