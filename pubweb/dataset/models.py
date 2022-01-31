from typing import TypedDict, List

from pubweb.clients.auth import Creds


class DatasetCreateResponse(TypedDict):
    datasetId: str
    credentials: Creds


class CreateDatasetRequest(TypedDict):
    name: str
    desc: str
    process: str
    project: str
    files: List
