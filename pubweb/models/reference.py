from dataclasses import dataclass
from pathlib import PurePath
from typing import List, Optional

from pubweb.models.file import File
from pubweb.models.validation import FileValidationSettings
from pubweb.utils import safe_load_json, find_first


@dataclass(frozen=True)
class ReferenceType:
    name: str
    description: str
    directory: str
    validation: List[FileValidationSettings]

    @classmethod
    def from_record(cls, record):
        validation = safe_load_json(record['validation'])
        return cls(record['name'], record['description'], record['directory'], validation)

    @property
    def id(self):
        return self.directory

    def validate(self):
        pass

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
        return find_first(self, lambda x: x.name == name)
