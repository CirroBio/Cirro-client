from typing import TypedDict, List, Optional


class DownloadArguments(TypedDict):
    project: str
    dataset: str
    data_directory: str
    interactive: bool


class UploadArguments(TypedDict):
    name: str
    description: str
    project: str
    process: str
    data_directory: str
    include_hidden: bool
    interactive: bool
    files: Optional[List[str]]


class ListArguments(TypedDict):
    project: str
    interactive: bool
