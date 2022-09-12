from typing import Optional

from pubweb.auth import AuthInfo, get_auth_info_from_config
from pubweb.clients import ApiClient
from pubweb.services import DatasetService, ProcessService, ProjectService, FileService, CommonService


class PubWeb:
    """
    A client for interacting with the PubWeb platform
    """
    def __init__(self, auth_info: Optional[AuthInfo] = None):
        if not auth_info:
            auth_info = get_auth_info_from_config()

        self._api_client = ApiClient(auth_info)
        self._file_service = FileService(self._api_client)
        self._dataset_service = DatasetService(self._api_client, self._file_service)
        self._project_service = ProjectService(self._api_client, self._file_service)
        self._process_service = ProcessService(self._api_client, self._file_service)
        self._common_service = CommonService(self._api_client)

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
