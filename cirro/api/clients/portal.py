from typing import Optional

from cirro.api.auth import AuthInfo, get_auth_info_from_config
from cirro.api.clients import ApiClient
from cirro.api.config import AppConfig
from cirro.api.services import DatasetService, ProcessService, ProjectService, FileService, CommonService


class DataPortalClient:
    """
    A client for interacting with the Cirro platform
    """
    def __init__(self, auth_info: Optional[AuthInfo] = None, base_url: str = None):
        self._configuration = AppConfig(base_url=base_url)
        if not auth_info:
            auth_info = get_auth_info_from_config(self._configuration)

        self._api_client = ApiClient(auth_info, data_endpoint=self._configuration.data_endpoint)
        self._file_service = FileService(self._api_client, self._configuration)
        self._dataset_service = DatasetService(self._api_client, self._file_service, self._configuration)
        self._project_service = ProjectService(self._api_client, self._file_service, self._configuration)
        self._process_service = ProcessService(self._api_client, self._file_service, self._configuration)
        self._common_service = CommonService(self._api_client, self._configuration)

    @property
    def dataset(self):
        return self._dataset_service

    @property
    def project(self):
        return self._project_service

    @property
    def process(self):
        return self._process_service

    @property
    def file(self):
        return self._file_service

    @property
    def common(self):
        return self._common_service
