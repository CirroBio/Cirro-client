import boto3
from requests.auth import AuthBase
from requests_aws4auth import AWS4Auth

from pubweb.api.auth.base import AuthInfo
from pubweb.api.config import config
from pubweb.api.models.auth import Creds


class IAMAuth(AuthInfo):
    """
    Uses AWS access tokens for authentication
    Note: this does not with any API calls at the moment
    """
    def __init__(self, access_key: str, secret_key: str, token: str = None):
        self.creds: Creds = {
            'AccessKeyId': access_key,
            'SecretAccessKey': secret_key,
            'SessionToken': token,
            'Expiration': None
        }

    @classmethod
    def load_current(cls):
        """
        Loads the current session's AWS credentials
        """
        current = boto3.Session().get_credentials().get_frozen_credentials()
        return cls(current.access_key, current.secret_key, current.token)

    def get_request_auth(self) -> AuthBase:
        return AWS4Auth(self.creds['AccessKeyId'],
                        self.creds['SecretAccessKey'],
                        config.region,
                        'appsync',
                        session_token=self.creds['SessionToken'])

    def get_current_user(self) -> str:
        sts_client = boto3.client('sts',
                                  aws_access_key_id=self.creds['AccessKeyId'],
                                  aws_secret_access_key=self.creds['SecretAccessKey'],
                                  aws_session_token=self.creds['SessionToken'])
        identity_arn = sts_client.get_caller_identity()['Arn']
        username = identity_arn.split('/')[-1]
        return f'iam-{username}'
