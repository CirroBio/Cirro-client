from typing import TypedDict, List, NamedTuple


class DatasetCreateResponse(TypedDict):
    datasetId: str
    dataPath: str


class CreateIngestDatasetInput(TypedDict):
    name: str
    description: str
    processId: str
    projectId: str
    files: List[str]


class Dataset:
    id: str
    name: str
    status: str
    desc: str


