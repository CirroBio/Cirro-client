from functools import partial
from typing import List

from attr import define
from cirro_api_client import CirroApiClient
from cirro_api_client.v1.api.file import generate_project_file_access_token
from cirro_api_client.v1.models import AWSCredentials

from cirro.clients.s3 import S3Client
from cirro.file_utils import upload_directory, download_directory
from cirro.models.file import FileAccessContext, File
from cirro.services.base import BaseService


@define
class FileService(BaseService):
    enable_additional_checksum: bool
    transfer_retries: int

    def get_access_credentials(self, project_id: str) -> AWSCredentials:
        return generate_project_file_access_token.sync(client=self._api_client, project_id=project_id, body=request)

    def get_file(self, file: File) -> bytes:
        """
        Gets the contents of a file
        """
        return self.get_file_from_path(file.access_context, file.relative_path)

    def get_file_from_path(self, access_context: FileAccessContext, file_path: str) -> bytes:
        """
        Gets the contents of a file by providing the path, used internally
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context),
                             self._configuration.region, self._configuration.enable_additional_checksum)
        full_path = f'{access_context.path_prefix}/{file_path}'.lstrip('/')
        return s3_client.get_file(access_context.bucket, full_path)

    def create_file(self, access_context: FileAccessContext, key: str,
                    contents: str, content_type: str):
        """
        Creates a file at the specified path
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context),
                             self._configuration.region, self._configuration.enable_additional_checksum)
        s3_client.create_object(key=key,
                                contents=contents,
                                content_type=content_type,
                                bucket=access_context.bucket)

    def upload_files(self, access_context: FileAccessContext, directory: str, files: List[str]):
        """
        Uploads a list of files from the specified directory
        :param access_context: File access context, use class methods to generate
        :param directory: base path to upload from
        :param files: relative path of files to upload
        :return:
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context),
                             self._configuration.region, self._configuration.enable_additional_checksum)
        upload_directory(directory, files, s3_client, access_context.bucket, access_context.path_prefix,
                         max_retries=self._configuration.transfer_max_retries)

    def download_files(self, access_context: FileAccessContext, directory: str, files: List[str]):
        """
        Download a list of files to the specified directory
        :param access_context: File access context, use class methods to generate
        :param directory: download location
        :param files: relative path of files to download
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context),
                             self._configuration.region, self._configuration.enable_additional_checksum)
        download_directory(directory, files, s3_client, access_context.bucket, access_context.path_prefix)


class FileEnabledService(BaseService):
    """
    Not to be instantiated directly
    """
    _file_service: FileService

    def __init__(self, api_client: CirroApiClient, file_service: FileService):
        super().__init__(api_client)
        self._file_service = file_service
