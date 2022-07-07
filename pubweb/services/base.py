from abc import ABC

from pubweb.clients import ApiClient


class BaseService(ABC):
    _api_client: ApiClient

    def __init__(self, api_client: ApiClient, **kwargs):
        self._api_client = api_client
