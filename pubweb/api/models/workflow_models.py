from typing import NamedTuple, List, Optional, Dict, TypedDict

from pubweb.api.models.process import ProcessRecord


class ProcessConfig(TypedDict):
    dynamo: ProcessRecord
    form: Dict
    input: Dict[str, str]
    output: Dict


class WorkflowRepository(NamedTuple):
    display_name: str
    org: str
    repo_name: str
    version: str
    entrypoint: str
    private: bool
    documentation_url: str
    tarball: Optional[str]

    @property
    def repo_path(self):
        return f'{self.org}/{self.repo_name}'


class Column(NamedTuple):
    header: str
    display_name: str
    description: str


class OptimizedOutput(NamedTuple):
    source_pattern: str
    seperator: str
    name: str
    description: str
    documentation_url: str
    columns: List[Column]
