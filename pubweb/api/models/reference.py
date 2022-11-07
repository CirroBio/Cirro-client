from dataclasses import dataclass
from pathlib import PurePath
from typing import Dict, Any, List, Optional
from pubweb.api.models.exceptions import DataPortalModelException

from pubweb.api.models.file import File
from pubweb.utils import safe_load_json


@dataclass(frozen=True)
class ReferenceType:
    name: str
    description: str
    directory: str
    validation: Dict[str, Any]

    @classmethod
    def from_record(cls, record):
        if record is None:
            raise DataPortalModelException("Cannot construct Dataset from null object.")
        validation = safe_load_json(record['validation'])
        return cls(record['name'], record['description'], record['directory'], validation)

    @property
    def id(self):
        return self.directory

    def __repr__(self):
        fields = f'name={self.name}'
        fields += f', description={self.description}'
        return f'{self.__class__.__name__}({fields})'


class Reference(File):
    @property
    def name(self):
        return PurePath(self.relative_path).parent.name

    def __str__(self):
        return self.name


class References(List[Reference]):
    def find_by_name(self, name: str) -> Optional[Reference]:
        return next((ref for ref in self if ref.name == name), None)
