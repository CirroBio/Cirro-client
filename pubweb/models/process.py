import json
from enum import Enum
from typing import NamedTuple, Dict, Any, TypedDict, List, Optional


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


class RunAnalysisCommand(NamedTuple):
    name: str
    description: str
    process_id: str
    parent_dataset_id: str
    project_id: str
    params: Dict[str, Any]
    notifications_emails: List[str]

    def to_json(self):
        try:
            param_json = json.dumps(self.params)
        except TypeError:
            raise RuntimeError('Params invalid')

        return {
            'name': self.name,
            'description': self.description,
            'processId': self.process_id,
            'parentDatasetId': self.parent_dataset_id,
            'projectId': self.project_id,
            'paramJson': param_json,
            'notificationEmails': self.notifications_emails
        }
