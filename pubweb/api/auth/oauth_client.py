from requests.auth import AuthBase

from pubweb.api.auth import AuthInfo


# TODO: Possible method of authenticating with API Keys
# since cognito auth doesn't work with federated login
class ClientAuth(AuthInfo):
    def get_request_auth(self) -> AuthBase:
        raise NotImplementedError()
