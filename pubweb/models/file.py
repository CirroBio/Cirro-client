from typing import Literal, TypedDict

AccessType = Literal['PROJECT', 'CHART', 'DATASET', 'RESOURCES']
FileOperation = Literal['UPLOAD', 'DOWNLOAD']


class S3AuthorizerInput(TypedDict):
    accessType: AccessType
    operation: FileOperation
    projectId: str
    datasetId: str


class FileAccessContext:
    def __init__(self, access_input: S3AuthorizerInput):
        """
        Prefer using class methods to instantiate
        """
        self.access_input = access_input

    @classmethod
    def download_dataset(cls, dataset_id: str, project_id: str):
        return cls({'accessType': 'DATASET', 'operation': 'DOWNLOAD',
                    'datasetId': dataset_id, 'projectId': project_id})

    @classmethod
    def upload_dataset(cls, dataset_id: str, project_id: str):
        return cls({'accessType': 'DATASET', 'operation': 'UPLOAD',
                    'datasetId': dataset_id, 'projectId': project_id})

    @property
    def query_variables(self):
        return self.access_input
