from typing import Literal, TypedDict, NamedTuple, Dict

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


class GetTokenQuery(NamedTuple):
    query: str
    variables: Dict


class S3AuthorizerInput(TypedDict):
    accessType: AccessType
    operation: FileOperation
    projectId: str
    datasetId: str


class FileAccessContext:
    def __init__(self,
                 access_input: S3AuthorizerInput,
                 bucket: str,
                 path: str = None):
        """
        Prefer using class methods to instantiate
        """
        self._access_input = access_input
        self.bucket = bucket
        self._path = path

    @classmethod
    def download_dataset(cls, dataset_id: str, project_id: str):
        return cls(
            {
                'accessType': 'DATASET', 'operation': 'DOWNLOAD',
                'datasetId': dataset_id, 'projectId': project_id
            },
            get_project_bucket(project_id),
            f'datasets/{dataset_id}'
        )

    @classmethod
    def upload_dataset(cls, dataset_id: str, project_id: str):
        return cls(
            {
                'accessType': 'DATASET', 'operation': 'UPLOAD',
                'datasetId': dataset_id, 'projectId': project_id
            },
            get_project_bucket(project_id),
            f'datasets/{dataset_id}/data'
        )

    @property
    def get_token_query(self) -> GetTokenQuery:
        return GetTokenQuery(_GET_FILE_ACCESS_TOKEN_QUERY, self._access_input)

    @property
    def path_prefix(self):
        return self._path
