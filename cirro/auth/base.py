from abc import ABC, abstractmethod
from typing import Callable, Dict

from attr import define
from cirro_api_client.cirro_auth import AuthMethod


@define
class RefreshableToken(AuthMethod):
    token_getter: Callable[[], str]

    def get_auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token_getter()}"}


class AuthInfo(ABC):
    @abstractmethod
    def get_current_user(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_auth_method(self) -> AuthMethod:
        raise NotImplementedError()
