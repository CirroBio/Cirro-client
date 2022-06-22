from pubweb.clients import ApiClient
from pubweb.clients.utils import GET_FILE_ACCESS_TOKEN_QUERY
from pubweb.models.auth import Creds
from pubweb.models.file import FileAccessContext
from pubweb.services.base import BaseService


def get_project_bucket(project_id):
    return f'z-{project_id}'


class FileService(BaseService):
    def get_access_credentials(self, access_context: FileAccessContext) -> Creds:
        credentials_response = self._api_client.query(GET_FILE_ACCESS_TOKEN_QUERY,
                                                      variables=access_context.query_variables)
        return credentials_response['getFileAccessToken']


class FileEnabledService(BaseService):
    _file_service: FileService

    def __init__(self, api_client: ApiClient, file_service: FileService):
        super(FileEnabledService, self).__init__(api_client)
        self._file_service = file_service
