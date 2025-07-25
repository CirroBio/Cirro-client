from pathlib import Path

from cirro_api_client.v1.models import Project, ReferenceType, ReferenceTypeValidationItem
from prompt_toolkit.validation import Validator, ValidationError

from cirro.cli.interactive.common_args import ask_project
from cirro.cli.interactive.utils import ask
from cirro.cli.models import UploadReferenceArguments
from cirro.helpers.references import get_matching_validation, format_expected_file


class ReferenceFileValidator(Validator):
    def __init__(self, validation: ReferenceTypeValidationItem):
        self.validation = validation

    def validate(self, document):
        file_path = Path(document.text)
        if not file_path.is_file() or len(document.text.strip()) == 0:
            raise ValidationError(
                message='Please enter a valid file',
                cursor_position=len(document.text)
            )
        matching = get_matching_validation(file_path.name, [self.validation])
        if not matching:
            raise ValidationError(
                message=f'File "{file_path.name}" does not match expected file: '
                        f'{format_expected_file(self.validation)}',
                cursor_position=len(document.text)
            )


def ask_reference_type(reference_types: list[ReferenceType], input_value: str = None) -> ReferenceType:
    reference_type_names = sorted([ref_type.name for ref_type in reference_types])
    reference_type_name = ask(
        'autocomplete',
        'What is the type of reference? (use TAB to display options)',
        choices=reference_type_names,
        default=input_value if input_value in reference_type_names else '',
        validate=lambda v: v.strip() != '' or 'This field is required'
    )
    for ref_type in reference_types:
        if ref_type.name == reference_type_name:
            return ref_type
    raise ValueError(f'Reference type "{reference_type_name}" not found')


def ask_name(input_value: str = None) -> str:
    return ask(
        'text',
        'What is the name of the reference?',
        default=input_value if input_value else '',
        validate=lambda v: v.strip() != '' or 'This field is required'
    )


def ask_reference_file_single(validation: ReferenceTypeValidationItem) -> Path:
    file_path = ask(
        'path',
        f'Please provide the path to {format_expected_file(validation)}',
        validate=ReferenceFileValidator(validation)
    )
    return Path(file_path)


def ask_reference_files(reference_type: ReferenceType) -> list[Path]:
    reference_files = []
    for validation in reference_type.validation:
        file_path = ask_reference_file_single(validation)
        reference_files.append(Path(file_path))
    return reference_files


def gather_reference_upload_arguments(input_params: UploadReferenceArguments,
                                      projects: list[Project],
                                      reference_types: list[ReferenceType]):
    input_params['project'] = ask_project(projects, input_params.get('project'))
    input_params['name'] = ask_name(input_params.get('name'))

    reference_type = ask_reference_type(reference_types, input_params.get('reference_type'))
    print('This reference type expects the following files:')
    for validation in reference_type.validation:
        print('  - ' + format_expected_file(validation))
    input_params['reference_type'] = reference_type.name

    files = ask_reference_files(reference_type)
    if len(files) == 0:
        raise ValueError("At least one reference file must be provided.")
    return input_params, files
