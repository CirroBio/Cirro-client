import json
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple, Dict, Any, TypedDict, List, Optional

from pubweb.api.models.exceptions import DataPortalModelException


class Executor(Enum):
    UNKNOWN = 'UNKNOWN'
    INGEST = 'INGEST'
    "Process type used when manually uploading files"
    NEXTFLOW = 'NEXTFLOW'
    "Processes that are ran using Nextflow"


@dataclass(frozen=True)
class ProcessCode:
    repository: str
    uri: str
    script: str
    version: str

    @classmethod
    def from_record(cls, record: Dict):
        if record is None:
            raise DataPortalModelException("Cannot construct Dataset from null object.")
        if not record:
            return None
        return cls(**record)


@dataclass(frozen=True)
class ProcessCompute:
    executor: str
    json: str
    name: str


@dataclass(frozen=True)
class Process:
    id: str
    name: str
    description: str
    child_process_ids: List[str]
    executor: Executor
    documentation_url: str
    code: ProcessCode
    form_spec_json: str
    sample_sheet_path: str
    file_requirements_message: str
    file_mapping_rules: List

    @classmethod
    def from_record(cls, record: 'ProcessRecord'):
        if record is None:
            raise DataPortalModelException("Cannot construct Dataset from null object.")
        return cls(
            record.get('id'),
            record.get('name'),
            record.get('desc'),
            record.get('childProcessIds'),
            Executor[record.get('executor')],
            record.get('documentationUrl'),
            ProcessCode.from_record(record.get('code', {})),
            record.get('formJson'),
            record.get('sampleSheetPath'),
            record.get('fileRequirementsMessage'),
            record.get('fileMappingRules'))


class ProcessRecord(TypedDict):
    id: str
    childProcessIds: List[str]
    name: str
    desc: str
    executor: str
    documentationUrl: str
    code: Dict
    paramDefaults: List
    computeDefaults: List[Dict]
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
        except TypeError as e:
            raise RuntimeError('Params invalid') from e

        return {
            'name': self.name,
            'description': self.description,
            'processId': self.process_id,
            'parentDatasetId': self.parent_dataset_id,
            'projectId': self.project_id,
            'paramJson': param_json,
            'notificationEmails': self.notifications_emails
        }
