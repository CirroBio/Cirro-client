from dataclasses import dataclass
from pathlib import PurePath
from typing import Literal, TypedDict, Optional

from pubweb.api.config import config
from pubweb.api.models.api import ApiQuery

AccessType = Literal['PROJECT', 'CHART', 'DATASET', 'RESOURCES']
FileOperation = Literal['UPLOAD', 'DOWNLOAD']
_GET_FILE_ACCESS_TOKEN_QUERY = '''
  query GetFileAccessToken($input: GetFileAccessTokenInput!) {
    getFileAccessToken(input: $input) {
      AccessKeyId
      Expiration
      SecretAccessKey
      SessionToken
    }
  }
'''


def get_project_bucket(project_id):
    return f'z-{project_id}'


class S3AuthorizerInput(TypedDict):
    accessType: AccessType
    operation: FileOperation
    projectId: Optional[str]
    datasetId: Optional[str]
    tokenLifetimeHours: Optional[int]


class DirectoryStatistics(TypedDict):
    size: float
    sizeFriendly: str
    numberOfFiles: int


class FileAccessContext:
    """
    Context holder for accessing various files in PubWeb and abstracting out their location
    Prefer to use the class methods to instantiate
    """
    def __init__(self,
                 access_input: S3AuthorizerInput,
                 bucket: str,
                 path: str = None):
        self._access_input = access_input
        self.bucket = bucket
        self._path = path

    @classmethod
    def download_dataset(cls, dataset_id: str, project_id: str):
        return cls(
            {
                'accessType': 'PROJECT', 'operation': 'DOWNLOAD',
                'datasetId': dataset_id, 'projectId': project_id,
                'tokenLifetimeHours': None
            },
            get_project_bucket(project_id),
            f'datasets/{dataset_id}'
        )

    @classmethod
    def upload_dataset(cls, dataset_id: str, project_id: str, token_lifetime_override: int = None):
        return cls(
            {
                'accessType': 'DATASET', 'operation': 'UPLOAD',
                'datasetId': dataset_id, 'projectId': project_id,
                'tokenLifetimeHours': token_lifetime_override
            },
            get_project_bucket(project_id),
            f'datasets/{dataset_id}/data'
        )

    @classmethod
    def download_project_resources(cls, project_id: str):
        return cls(
            {
                'accessType': 'PROJECT', 'operation': 'DOWNLOAD',
                'projectId': project_id, 'datasetId': None,
                'tokenLifetimeHours': None
            },
            get_project_bucket(project_id),
            'resources'
        )

    @classmethod
    def upload_project_resources(cls, project_id: str):
        return cls(
            {
                'accessType': 'PROJECT', 'operation': 'UPLOAD',
                'projectId': project_id, 'datasetId': None,
                'tokenLifetimeHours': None
            },
            get_project_bucket(project_id),
            'resources/data'
        )

    @classmethod
    def resources(cls):
        return cls(
            {
                'accessType': 'RESOURCES', 'operation': 'DOWNLOAD',
                'projectId': None, 'datasetId': None,
                'tokenLifetimeHours': None
            },
            config.resources_bucket,
            ''
        )

    @property
    def get_token_query(self) -> ApiQuery:
        """ Used to fetch access token """
        return ApiQuery(
            query=_GET_FILE_ACCESS_TOKEN_QUERY,
            variables={'input': self._access_input}
        )

    @property
    def path_prefix(self):
        return self._path

    @property
    def domain(self):
        return f's3://{self.bucket}/{self.path_prefix}'


@dataclass(frozen=True)
class File:
    relative_path: str
    size: int
    access_context: FileAccessContext

    @classmethod
    def of(cls, file: 'File'):
        return cls(file.relative_path, file.size, file.access_context)

    @property
    def absolute_path(self):
        return f'{self.access_context.domain}/{self.relative_path.strip("/")}'

    @property
    def name(self):
        return PurePath(self.absolute_path).name

    def __repr__(self):
        return f'{self.__class__.__name__}(path={self.relative_path})'
