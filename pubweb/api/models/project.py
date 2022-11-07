from dataclasses import dataclass

from pubweb.api.config import config
from pubweb.api.models.exceptions import DataPortalModelException


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    description: str

    @classmethod
    def from_record(cls, record):
        if record is None:
            raise DataPortalModelException("Cannot construct Dataset from null object.")
        return cls(record['id'],
                   record['name'],
                   record['desc'])

    @property
    def url(self):
        return f'{config.base_url}/projects/{self.id}'
