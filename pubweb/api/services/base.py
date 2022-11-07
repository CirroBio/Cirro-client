from abc import ABC

from pubweb.api.clients import ApiClient


class BaseService(ABC):
    _api_client: ApiClient

    def __init__(self, api_client: ApiClient):
        self._api_client = api_client
