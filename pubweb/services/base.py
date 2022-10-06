from abc import ABC

from pubweb.clients import ApiClient
from pubweb.config import AppConfig


class BaseService(ABC):
    _api_client: ApiClient
    _configuration: AppConfig

    def __init__(self, api_client: ApiClient, configuration: AppConfig):
        self._api_client = api_client
        self._configuration = configuration
