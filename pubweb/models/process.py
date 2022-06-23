from enum import Enum
from typing import TypedDict, List, Optional


class Executor(Enum):
    INGEST = 'INGEST'
    "Process type used when manually uploading files"
    NEXTFLOW = 'NEXTFLOW'
    "Processes that are ran using Nextflow"


class ProcessCode(TypedDict):
    repository: str
    uri: str
    script: str
    version: str


class ProcessCompute(TypedDict):
    executor: str
    json: str
    name: str


class Process(TypedDict):
    id: str
    childProcessIds: List[str]
    name: str
    desc: str
    executor: str
    documentationUrl: str
    code: ProcessCode
    paramDefaults: List
    computeDefaults: List[ProcessCompute]
    paramMapJson: str
    formJson: str
    fileJson: str
    componentJson: str
    infoJson: str
    webOptimizationJson: str
    preProcessScript: str
    sampleSheetPath: Optional[str]
    fileRequirementsMessage: str
    fileMappingRules: List
