from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, List, Any, Dict

from cirro.api.models.exceptions import DataPortalModelException
from cirro.api.models.status import Status
from cirro.utils import parse_json_date, safe_load_json


class DatasetCreateResponse(TypedDict):
    datasetId: str
    dataPath: str


@dataclass
class CreateIngestDatasetInput:
    name: str
    description: str
    process_id: str
    project_id: str
    files: List[str]

    def to_json(self):
        return {
            'name': self.name,
            'description': self.description,
            'processId': self.process_id,
            'projectId': self.project_id,
            'files': self.files
        }


@dataclass(frozen=True)
class Dataset:
    id: str
    name: str
    description: str
    process_id: str
    project_id: str
    status: Status
    source_dataset_ids: List[str]
    info: Dict[str, Any]
    params: Dict[str, Any]
    created_at: datetime

    @classmethod
    def from_record(cls, record):
        if record is None:
            raise DataPortalModelException("Cannot construct Dataset from null object.")
        return cls(
            record.get('id'),
            record.get('name'),
            record.get('desc'),
            record.get('process'),
            record.get('project'),
            Status[record.get('status')],
            record.get('sourceDatasets'),
            safe_load_json(record.get('infoJson')),
            safe_load_json(record.get('paramJson')),
            parse_json_date(record.get('createdAt'))
        )

    @property
    def relative_url(self):
        return f'projects/{self.project_id}/dataset/{self.id}'
