from typing import TypedDict, List

from pubweb.auth import Creds


class DatasetCreateResponse(TypedDict):
    datasetId: str
    credentials: Creds


class DatasetInput(TypedDict):
    name: str
    desc: str
    process: str
    project: str
    files: List
