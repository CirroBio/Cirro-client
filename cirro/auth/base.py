from abc import ABC, abstractmethod

from cirro_api_client.cirro_auth import AuthMethod


class AuthInfo(ABC):
    @abstractmethod
    def get_current_user(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_auth_method(self) -> AuthMethod:
        raise NotImplementedError()
