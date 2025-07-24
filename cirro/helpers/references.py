from pathlib import Path
from typing import Optional

from cirro_api_client.v1.models import ReferenceType, ReferenceTypeValidationItem

from cirro.models.file import PathLike
from cirro.models.reference import ReferenceValidation


def format_expected_file(validation: ReferenceTypeValidationItem):
    save_as = validation.additional_properties.get('saveAs')
    if glob := validation.additional_properties.get('glob'):
        return f'{glob} (e.g., {save_as})'
    file_type = validation.additional_properties.get('fileType')
    return f'.{file_type} (e.g., {save_as})'


def get_matching_validation(file_name: str,
                            validations: list[ReferenceTypeValidationItem]) -> Optional[ReferenceValidation]:
    for validation in validations:
        validation_dict: ReferenceValidation = validation.to_dict()
        glob_pattern = validation_dict.get('glob')
        if glob_pattern and Path(file_name).match(validation_dict.get('glob')):
            return validation_dict
        if file_name.endswith(validation_dict['fileType']):
            return validation_dict
    return None


def _get_reference_upload_file_name(file: PathLike, reference_type: ReferenceType) -> str:
    if not isinstance(file, Path):
        file = Path(file)
    file_name = file.name

    matching_validation = get_matching_validation(file_name=file_name, validations=reference_type.validation)
    return matching_validation.get('saveAs') \
        if matching_validation and matching_validation.get('saveAs') \
        else file_name


def generate_reference_file_path_map(files: list[PathLike],
                                     name: str,
                                     ref_type: ReferenceType):
    """
    Generate a mapping of reference files to their upload paths based on the reference type.

    Files are uploaded to an expected directory structure based on the reference type.
    For example, <reference_id>/<reference_name>/<normalized_file_name>
    """
    upload_prefix = Path(ref_type.directory, name)

    file_path_map = {
        reference_file: (upload_prefix / _get_reference_upload_file_name(reference_file, ref_type)).as_posix()
        for reference_file in files
    }
    return file_path_map
