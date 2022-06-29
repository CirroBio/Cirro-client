import boto3
from requests.auth import AuthBase
from requests_aws4auth import AWS4Auth

from pubweb import config
from pubweb.auth import AuthInfo
from pubweb.models.auth import Creds


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
