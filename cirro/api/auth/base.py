from abc import ABC, abstractmethod
from typing import Callable

from requests.auth import AuthBase


class AuthInfo(ABC):
    @abstractmethod
    def get_request_auth(self) -> AuthBase:
        raise NotImplementedError()

    @abstractmethod
    def get_current_user(self) -> str:
        raise NotImplementedError()


class RequestAuthWrapper(AuthBase):
    def __init__(self, token_getter: Callable[..., str]):
        self.token_getter = token_getter

    def __call__(self, request):
        request.headers['Authorization'] = self.token_getter()
        return request
