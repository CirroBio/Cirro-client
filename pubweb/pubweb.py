from pubweb.auth import AuthInfo
from pubweb.clients import ApiClient
from pubweb.services import DatasetService, ProcessService, ProjectService, FileService


class PubWeb:
    def __init__(self, auth_info: AuthInfo):
        self._api_client = ApiClient(auth_info)
        self._file_service = FileService(self._api_client)
        self._dataset_service = DatasetService(self._api_client, self._file_service)
        self._project_service = ProjectService(self._api_client)
        self._process_service = ProcessService(self._api_client)

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
