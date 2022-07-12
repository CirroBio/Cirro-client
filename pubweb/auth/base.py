from abc import ABC, abstractmethod

from requests.auth import AuthBase


class AuthInfo(ABC):
    @abstractmethod
    def get_request_auth(self) -> AuthBase:
        raise NotImplementedError()

    @abstractmethod
    def get_current_user(self) -> str:
        raise NotImplementedError()
