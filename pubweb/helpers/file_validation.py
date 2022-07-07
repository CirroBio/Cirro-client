from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class FileValidationSettings:
    fileType: str
    saveAs: str
    glob: Optional[str]


class BaseValidator:
    pass


def get_file_validator(file: Path, validation_settings: List[FileValidationSettings]) -> FileValidator:
    for setting in validation_settings:
        if validation_settings.get('glob'):
            return file.match(validation_settings['glob'])
