from typing import TypedDict

import boto3
from boto3 import Session
from pycognito import AWSSRP
from requests.auth import AuthBase
from requests_aws4auth import AWS4Auth

from pubweb import config

SERVICE_NAME = 'appsync'


class Creds(TypedDict):
    AccessKeyId: str
    Expiration: str
    SecretAccessKey: str
    SessionToken: str


class AuthInfo:
    def get_request_auth(self) -> AuthBase:
        pass


class CognitoAuthInfo(AuthInfo):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_request_auth(self) -> AuthBase:
        return self.RequestAuth(self._get_token()['AccessToken'])

    def _get_token(self):
        cognito = boto3.client('cognito-idp')
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


# Not used
class IamAuthInfo(AuthInfo):
    def __init__(self,
                 access_key=None,
                 secret_key=None,
                 session_token=None,
                 region=None):
        if not access_key:
            aws = Session()
            print(f'Using profile: {aws.profile_name}')
            credentials = aws.get_credentials().get_frozen_credentials()
            self.access_key = credentials.access_key
            self.secret_key = credentials.secret_key
            self.session_token = credentials.token
            self.region = aws.region_name
        else:
            self.access_key = access_key
            self.secret_key = secret_key
            self.session_token = session_token
            self.region = region

    def get_request_auth(self) -> AuthBase:
        auth = AWS4Auth(self.access_key,
                        self.access_key,
                        region=self.region,
                        service=SERVICE_NAME,
                        session_token=self.session_token)
        return auth
