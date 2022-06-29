import boto3
from pycognito import AWSSRP
from requests.auth import AuthBase

from pubweb import config
from pubweb.auth import AuthInfo


class UsernameAndPasswordAuth(AuthInfo):
    """
    Uses your username & password to authenticate
    Note: this does not work with federated identities (Fred Hutch login)
    You must contact HDC to manually create an account
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_request_auth(self) -> AuthBase:
        return self.RequestAuth(self._get_token()['AccessToken'])

    def _get_token(self):
        cognito = boto3.client('cognito-idp', region_name=config.region)
        aws = AWSSRP(username=self.username,
                     password=self.password,
                     pool_id=config.user_pool_id,
                     client_id=config.app_id,
                     client=cognito)
        resp = aws.authenticate_user()
        return resp['AuthenticationResult']

    class RequestAuth(AuthBase):
        def __init__(self, token):
            self.token = token

        def __call__(self, request):
            request.headers['Authorization'] = self.token
            return request
