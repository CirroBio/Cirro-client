import threading
from datetime import datetime, timezone
from functools import partial
from typing import List, Dict

from attr import define
from cirro_api_client import CirroApiClient
from cirro_api_client.v1.api.file import generate_project_file_access_token
from cirro_api_client.v1.models import AWSCredentials, AccessType

from cirro.clients.s3 import S3Client
from cirro.file_utils import upload_directory, download_directory
from cirro.models.file import FileAccessContext, File
from cirro.services.base import BaseService


@define
class FileService(BaseService):
    enable_additional_checksum: bool
    transfer_retries: int
    _get_token_lock = threading.Lock()
    _read_token_cache: Dict[str, AWSCredentials] = {}

    def get_access_credentials(self, access_context: FileAccessContext) -> AWSCredentials:
        """
        Retrieves credentials to access files
        """
        access_request = access_context.file_access_request
        if access_request.access_type == AccessType.PROJECT_DOWNLOAD:
            return self._get_project_read_credentials(access_context)
        return generate_project_file_access_token.sync(client=self._api_client,
                                                       project_id=access_context.project_id,
                                                       body=access_context.file_access_request)

    def _get_project_read_credentials(self, access_context: FileAccessContext):
        """
        Retrieves credentials to read project data, this can be cached
        """
        access_request = access_context.file_access_request
        project_id = access_context.project_id
        with self._get_token_lock:
            cached_token = self._read_token_cache.get(project_id)

            if not cached_token or datetime.now(tz=timezone.utc) > cached_token.expiration:
                new_token = generate_project_file_access_token.sync(client=self._api_client,
                                                                    project_id=project_id,
                                                                    body=access_request)
                self._read_token_cache[project_id] = new_token

        return self._read_token_cache[project_id]

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
                             self.enable_additional_checksum)
        full_path = f'{access_context.prefix}/{file_path}'.lstrip('/')
        return s3_client.get_file(access_context.bucket, full_path)

    def create_file(self, access_context: FileAccessContext, key: str,
                    contents: str, content_type: str):
        """
        Creates a file at the specified path
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context),
                             self.enable_additional_checksum)
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
                             self.enable_additional_checksum)
        upload_directory(directory, files, s3_client, access_context.bucket, access_context.prefix,
                         max_retries=self.transfer_retries)

    def download_files(self, access_context: FileAccessContext, directory: str, files: List[str]):
        """
        Download a list of files to the specified directory
        :param access_context: File access context, use class methods to generate
        :param directory: download location
        :param files: relative path of files to download
        """
        s3_client = S3Client(partial(self.get_access_credentials, access_context),
                             self.enable_additional_checksum)
        download_directory(directory, files, s3_client, access_context.bucket, access_context.prefix)


class FileEnabledService(BaseService):
    """
    Not to be instantiated directly
    """
    _file_service: FileService

    def __init__(self, api_client: CirroApiClient, file_service: FileService):
        super().__init__(api_client)
        self._file_service = file_service
