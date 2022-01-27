import boto3
from boto3 import Session
from botocore.client import BaseClient
from requests.auth import AuthBase
from requests_aws4auth import AWS4Auth

CLIENT_ID = '7ic2n55r9h4fj0qej5q9ikr2o1'
SERVICE_NAME = 'appsync'


class AuthInfo:
    def get_request_auth(self) -> AuthBase:
        pass

    def get_client(self, client_name) -> BaseClient:
        pass


class CognitoAuthInfo(AuthInfo):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_request_auth(self) -> AuthBase:
        return self.RequestAuth(self._get_access_token())

    def get_client(self, client_name):
        creds = self._get_iam_creds()
        return boto3.client(client_name,
                            aws_access_key_id=creds['accessKey'],
                            aws_secret_access_key=creds['secretKey'],
                            aws_session_token=creds['sessionToken'])

    def _get_access_token(self):
        cognito = boto3.client('cognito-idp')
        resp = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': self.username,
                'PASSWORD': self.password
            }
        )
        token = resp['AuthenticationResult']['AccessToken']
        return token

    def _get_iam_creds(self):
        return {
            'accessKey': '',
            'secretKey': '',
            'sessionToken': ''
        }

    class RequestAuth(AuthBase):
        def __init__(self, token):
            self.token = token

        def __call__(self, request):
            request.headers['Authorization'] = self.token
            return request


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

    def get_client(self, client_name) -> BaseClient:
        return boto3.client(client_name,
                            aws_access_key_id=self.access_key,
                            aws_secret_access_key=self.secret_key,
                            aws_session_token=self.session_token)

    def get_request_auth(self) -> AuthBase:
        auth = AWS4Auth(self.access_key,
                        self.access_key,
                        region=self.region,
                        service=SERVICE_NAME,
                        session_token=self.session_token)
        return auth
