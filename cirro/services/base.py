from abc import ABC

from attr import define
from cirro_api_client import CirroApiClient

from cirro.config import AppConfig


@define
class BaseService(ABC):
    _api_client: CirroApiClient
