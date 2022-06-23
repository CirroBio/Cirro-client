from typing import Literal, TypedDict

AccessType = Literal['PROJECT', 'CHART', 'DATASET', 'RESOURCES']
FileOperation = Literal['UPLOAD', 'DOWNLOAD']


def get_project_bucket(project_id):
    return f'z-{project_id}'


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
        self.access_input = access_input
        self.bucket = bucket
        self.path = path

    @classmethod
    def download_dataset(cls, dataset_id: str, project_id: str):
        return cls(
            {
                'accessType': 'DATASET', 'operation': 'DOWNLOAD',
                'datasetId': dataset_id, 'projectId': project_id
            },
            f'datasets/{dataset_id}',
            get_project_bucket(project_id)
        )

    @classmethod
    def upload_dataset(cls, dataset_id: str, project_id: str):
        return cls(
            {
                'accessType': 'DATASET', 'operation': 'UPLOAD',
                'datasetId': dataset_id, 'projectId': project_id
            },
            f'datasets/{dataset_id}/data',
            get_project_bucket(project_id)
        )

    @property
    def query_variables(self):
        return self.access_input

    @property
    def path_prefix(self):
        return self.path
