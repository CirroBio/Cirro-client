from typing import TypedDict, List


class DatasetCreateResponse(TypedDict):
    datasetId: str
    dataPath: str


class CreateIngestDatasetInput(TypedDict):
    name: str
    description: str
    processId: str
    projectId: str
    files: List[str]
