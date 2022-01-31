from boto3 import Session
from requests.auth import AuthBase
from requests_aws4auth import AWS4Auth

from pubweb.auth.base import AuthInfo

SERVICE_NAME = 'appsync'


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
