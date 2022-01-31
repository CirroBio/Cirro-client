from typing import TypedDict, List

from pubweb.models.auth import Creds


class DatasetCreateResponse(TypedDict):
    datasetId: str
    credentials: Creds


class CreateDatasetRequest(TypedDict):
    name: str
    desc: str
    process: str
    project: str
    files: List
