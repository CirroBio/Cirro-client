from typing import TypedDict


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
    interactive: bool
    use_third_party_tool: bool


class ListArguments(TypedDict):
    project: str
    interactive: bool
