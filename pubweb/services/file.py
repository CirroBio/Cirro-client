import json
from functools import partial
from typing import List

from pubweb.auth.iam import IAMAuth
from pubweb.clients import ApiClient, S3Client
from pubweb.file_utils import upload_directory, download_directory
from pubweb.models.auth import Creds
from pubweb.models.file import FileAccessContext, File
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

    def get_file(self, file: File) -> str:
        """
        Gets the string contents of a file
        """
        return self.get_file_from_path(file.access_context, file.relative_path)

    def get_file_from_path(self, access_context: FileAccessContext, file_path: str) -> str:
        """
        Gets the string contents of a file by providing the path, used internally
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context))
        full_path = f'{access_context.path_prefix}/{file_path}'.lstrip('/')
        return s3_client.get_file(access_context.bucket, full_path)

    def upload_files(self, access_context: FileAccessContext, directory: str, files: List[str]):
        """
        Uploads a list of files from the specified directory
        :param access_context: File access context, use class methods to generate
        :param directory: base path to upload from
        :param files: relative path of files to upload
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

    def get_file_listing(self, access_context: FileAccessContext) -> List[File]:
        """
        Gets a listing of files of the current access context,
        note that this expects a manifest.json file
        :param access_context: File access context, use class methods to generate
        :return: relative path of files
        """
        file = self.get_file_from_path(access_context, 'web/manifest.json')
        manifest = json.loads(file)
        return [File(file['file'], file['size'], access_context)
                for file in manifest['files']]


class FileEnabledService(BaseService):
    """
    Not to be instantiated directly
    """
    _file_service: FileService

    def __init__(self, api_client: ApiClient, file_service: FileService):
        super().__init__(api_client)
        self._file_service = file_service
