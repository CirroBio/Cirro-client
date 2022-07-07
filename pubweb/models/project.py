from dataclasses import dataclass

from pubweb.config import config


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    description: str

    @classmethod
    def from_record(cls, json):
        return cls(json['id'],
                   json['name'],
                   json['desc'])

    @property
    def url(self):
        return f'{config.base_url}/projects/{self.id}'
