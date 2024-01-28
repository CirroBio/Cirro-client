from abc import ABC

from attr import define
from cirro_api_client import CirroApiClient


@define
class BaseService(ABC):
    _api_client: CirroApiClient
