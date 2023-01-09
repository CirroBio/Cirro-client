from dataclasses import dataclass

from cirro.api.models.exceptions import DataPortalModelException


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
    def relative_url(self):
        return f'projects/{self.id}'
