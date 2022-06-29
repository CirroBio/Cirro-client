from functools import partial
from typing import List

from pubweb.auth import IAMAuth
from pubweb.clients import ApiClient, S3Client
from pubweb.file_utils import upload_directory, download_directory
from pubweb.models.auth import Creds
from pubweb.models.file import FileAccessContext
from pubweb.services.base import BaseService


class FileService(BaseService):
    def get_access_credentials(self, access_context: FileAccessContext) -> Creds:
        # Special case:
        # we do not need to call the API to get IAM creds if we are using IAM creds
        if isinstance(self._api_client.auth_info, IAMAuth):
            return self._api_client.auth_info.creds
        # Call API to get temporary credentials
        credentials_response = self._api_client.query(*access_context.get_token_query)
        return credentials_response['getFileAccessToken']

    def get_file(self, access_context: FileAccessContext, file_path: str) -> str:
        """
        Gets the string contents of an individual file
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context))
        full_path = f'{access_context.path_prefix}/{file_path}'
        return s3_client.get_file(access_context.bucket, full_path)

    def upload_files(self, access_context: FileAccessContext, directory: str, files: List[str]):
        """
        Uploads a list of files from the specified directory
        :param access_context: File access context, use class methods to generate
        :param directory: base path to upload from
        :param files: relative path of files to upload
        :return:
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context))
        upload_directory(directory, files, s3_client, access_context.bucket, access_context.path_prefix)

    def download_files(self, access_context: FileAccessContext, directory: str, files: List[str]):
        """
        Download a list of files to the specified directory
        :param access_context: File access context, use class methods to generate
        :param directory: download location
        :param files: relative path of files to download
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context))
        download_directory(directory, files, s3_client, access_context.bucket, access_context.path_prefix)


class FileEnabledService(BaseService):
    """
    Not to be instantiated directly
    """
    _file_service: FileService

    def __init__(self, api_client: ApiClient, file_service: FileService):
        super(FileEnabledService, self).__init__(api_client)
        self._file_service = file_service
