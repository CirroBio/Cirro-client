from abc import ABC

from requests.auth import AuthBase


class AuthInfo(ABC):
    def get_request_auth(self) -> AuthBase:
        pass
