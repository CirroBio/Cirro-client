import logging
import threading
from datetime import datetime, timedelta

import boto3
from pycognito import AWSSRP
from requests.auth import AuthBase

from cirro.api.auth.base import AuthInfo, RequestAuthWrapper

logger = logging.getLogger()


class UsernameAndPasswordAuth(AuthInfo):
    """
    Uses your username & password to authenticate
    Note: this does not work with federated identities (Fred Hutch login)
    You must contact HDC to manually create an account
    """
    def __init__(self, username: str, password: str, region: str, user_pool_id: str, client_id: str):
        self.region = region
        self.client_id = client_id
        self.user_pool_id = user_pool_id
        self._username = username
        self._password = password
        self._auth_result = None
        self._get_token_lock = threading.Lock()
        self.token_expiry = None

    def get_request_auth(self) -> AuthBase:
        return RequestAuthWrapper(lambda: self._get_token()['AccessToken'])

    def get_current_user(self) -> str:
        return self._username

    def _get_token(self):
        if self.token_expiry and self.token_expiry > datetime.now():
            return self._auth_result

        with self._get_token_lock:
            logger.debug('Fetching new token from cognito')
            cognito = boto3.client('cognito-idp', region_name=self.region)
            aws = AWSSRP(username=self._username,
                         password=self._password,
                         pool_id=self.user_pool_id,
                         client_id=self.client_id,
                         client=cognito)
            resp = aws.authenticate_user()
            self._auth_result = resp['AuthenticationResult']
            self.access_token_expiry = datetime.now() + timedelta(seconds=self._auth_result['ExpiresIn'])
            return self._auth_result
