import threading
from datetime import datetime, timezone
from functools import partial
from typing import List, Dict

from cirro_api_client import CirroApiClient
from cirro_api_client.v1.api.file import generate_project_file_access_token
from cirro_api_client.v1.models import AWSCredentials, AccessType

from cirro.clients.s3 import S3Client
from cirro.file_utils import upload_directory, download_directory
from cirro.models.file import FileAccessContext, File, PathLike
from cirro.services.base import BaseService


class FileService(BaseService):
    """
    Service for interacting with files
    """
    enable_additional_checksum: bool
    transfer_retries: int
    _get_token_lock = threading.Lock()
    _read_token_cache: Dict[str, AWSCredentials] = {}

    def __init__(self, api_client, enable_additional_checksum, transfer_retries):
        """
        Instantiates the file service class
        """
        self._api_client = api_client
        self.enable_additional_checksum = enable_additional_checksum
        self.transfer_retries = transfer_retries

    def get_access_credentials(self, access_context: FileAccessContext) -> AWSCredentials:
        """
        Retrieves credentials to access files

        Args:
            access_context (cirro.models.file.FileAccessContext): File access context, use class methods to generate
        """
        access_request = access_context.file_access_request

        if access_request.access_type == AccessType.PROJECT_DOWNLOAD:
            return self._get_project_read_credentials(access_context)

        else:
            return generate_project_file_access_token.sync(
                client=self._api_client,
                project_id=access_context.project_id,
                body=access_context.file_access_request
            )

    def _get_project_read_credentials(self, access_context: FileAccessContext):
        """
        Retrieves credentials to read project data, this can be cached
        """
        access_request = access_context.file_access_request
        project_id = access_context.project_id
        with self._get_token_lock:
            cached_token = self._read_token_cache.get(project_id)

            if not cached_token or datetime.now(tz=timezone.utc) > cached_token.expiration:
                new_token = generate_project_file_access_token.sync(
                    client=self._api_client,
                    project_id=project_id,
                    body=access_request
                )

                self._read_token_cache[project_id] = new_token

        return self._read_token_cache[project_id]

    def get_file(self, file: File) -> bytes:
        """
        Gets the contents of a file

        Args:
            file (cirro.models.file.File):

        Returns:
            The raw bytes of the file
        """
        return self.get_file_from_path(file.access_context, file.relative_path)

    def get_file_from_path(self, access_context: FileAccessContext, file_path: str) -> bytes:
        """
        Gets the contents of a file by providing the path, used internally

        Args:
            access_context (cirro.models.file.FileAccessContext): File access context, use class methods to generate
            file_path (str): Relative path to file within dataset

        Returns:
            The raw bytes of the file
        """

        s3_client = S3Client(
            partial(self.get_access_credentials, access_context),
            self.enable_additional_checksum
        )

        full_path = f'{access_context.prefix}/{file_path}'.lstrip('/')

        return s3_client.get_file(access_context.bucket, full_path)

    def create_file(self, access_context: FileAccessContext, key: str,
                    contents: str, content_type: str) -> None:
        """
        Creates a file at the specified path

        Args:
            access_context (cirro.models.file.FileAccessContext): File access context, use class methods to generate
            key (str): Key of object to create
            contents (str): Content of object
            content_type (str):
        """

        s3_client = S3Client(
            partial(self.get_access_credentials, access_context),
            self.enable_additional_checksum
        )

        s3_client.create_object(
            key=key,
            contents=contents,
            content_type=content_type,
            bucket=access_context.bucket
        )

    def upload_files(self,
                     access_context: FileAccessContext,
                     directory: PathLike,
                     files: List[PathLike]) -> None:
        """
        Uploads a list of files from the specified directory

        Args:
            access_context (cirro.models.file.FileAccessContext): File access context, use class methods to generate
            directory (str|Path): Path to directory
            files (typing.List[str|Path]): List of paths to files within the directory
                must be the same type as directory.
        """

        s3_client = S3Client(
            partial(self.get_access_credentials, access_context),
            self.enable_additional_checksum
        )

        upload_directory(
            directory,
            files,
            s3_client,
            access_context.bucket,
            access_context.prefix,
            max_retries=self.transfer_retries
        )

    def download_files(self, access_context: FileAccessContext, directory: str, files: List[str]) -> None:
        """
        Download a list of files to the specified directory

        Args:
            access_context (cirro.models.file.FileAccessContext): File access context, use class methods to generate
            directory (str): download location
            files (List[str]): relative path of files to download
        """
        s3_client = S3Client(
            partial(self.get_access_credentials, access_context),
            self.enable_additional_checksum
        )

        download_directory(
            directory,
            files,
            s3_client,
            access_context.bucket,
            access_context.prefix
        )


class FileEnabledService(BaseService):
    """
    Not to be instantiated directly
    """
    _file_service: FileService

    def __init__(self, api_client: CirroApiClient, file_service: FileService):
        super().__init__(api_client)
        self._file_service = file_service
