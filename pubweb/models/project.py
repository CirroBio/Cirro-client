from dataclasses import dataclass


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
    def relative_url(self):
        return f'projects/{self.id}'
