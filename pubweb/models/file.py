from typing import Literal, TypedDict, Optional

from pubweb.models.api import ApiQuery

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
    projectId: str
    datasetId: Optional[str]
    tokenLifetimeHours: Optional[int]


class DirectoryStatistics(TypedDict):
    size: float
    sizeFriendly: str
    numberOfFiles: int


class FileAccessContext:
    """
    Context holder for accessing various files in PubWeb and abstracting out their location
    Supports dataset paths
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

    # TODO: support reference upload

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
