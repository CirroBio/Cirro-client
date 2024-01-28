from dataclasses import dataclass
from pathlib import PurePath
from typing import TypedDict, Dict, Optional

from cirro_api_client.v1.models import FileAccessRequest, AccessType, FileEntry

from cirro.models.s3_path import S3Path


class DirectoryStatistics(TypedDict):
    size: float
    sizeFriendly: str
    numberOfFiles: int


class FileAccessContext:
    """
    Context holder for accessing various files in Cirro and abstracting out their location
    Prefer to use the class methods to instantiate
    """
    def __init__(self,
                 file_access_request: FileAccessRequest,
                 project_id: str,
                 base_url: str):
        self.file_access_request = file_access_request
        self.base_url = base_url
        self.project_id = project_id
        self._s3_path = S3Path(base_url)

    @classmethod
    def download(cls, project_id: str, base_url: str, token_lifetime_override: int = None):
        return cls(
            file_access_request=FileAccessRequest(
                access_type=AccessType.PROJECT_DOWNLOAD,
                token_lifetime_hours=token_lifetime_override
            ),
            base_url=base_url,
            project_id=project_id
        )

    @classmethod
    def upload_dataset(cls, project_id: str, dataset_id: str, base_url: str, token_lifetime_override: int = None):
        return cls(
            file_access_request=FileAccessRequest(
                access_type=AccessType.DATASET_UPLOAD,
                dataset_id=dataset_id,
                token_lifetime_hours=token_lifetime_override
            ),
            base_url=base_url,
            project_id=project_id
        )

    @classmethod
    def upload_reference(cls, project_id: str, base_url: str):
        return cls(
            file_access_request=FileAccessRequest(
                access_type=AccessType.REFERENCE_UPLOAD
            ),
            base_url=base_url,
            project_id=project_id
        )

    @classmethod
    def upload_sample_sheet(cls, project_id: str, dataset_id: str, base_url: str):
        return cls(
            file_access_request=FileAccessRequest(
                access_type=AccessType.SAMPLESHEET_UPLOAD,
                dataset_id=dataset_id
            ),
            base_url=base_url,
            project_id=project_id
        )

    @property
    def bucket(self):
        return self._s3_path.bucket

    @property
    def prefix(self):
        return self._s3_path.key


@dataclass(frozen=True)
class File:
    relative_path: str
    size: int
    access_context: FileAccessContext
    metadata: Optional[Dict] = None

    @classmethod
    def from_file_entry(cls, file: FileEntry, project_id: str, domain: str = None):
        # Path is absolute rather than relative
        if 's3://' in file.path:
            parts = S3Path(file.path)
            domain = parts.base
            path = parts.key
        else:
            path = file.path

        return cls(
            relative_path=path,
            metadata=file.metadata.additional_properties,
            size=file.size,
            access_context=FileAccessContext.download(project_id=project_id, base_url=domain)
        )

    @property
    def absolute_path(self):
        return f'{self.access_context.base_url}/{self.relative_path.strip("/")}'

    @property
    def name(self):
        return PurePath(self.absolute_path).name

    def __repr__(self):
        return f'{self.__class__.__name__}(path={self.relative_path})'
