import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import List

from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.validation import Validator, ValidationError
from questionary import Choice

from cirro.api.models.process import Process
from cirro.api.models.project import Project
from cirro.cli.interactive.common_args import ask_project
from cirro.cli.interactive.utils import ask
from cirro.cli.models import UploadArguments
from cirro.file_utils import get_directory_stats, get_files_in_directory


class DataDirectoryValidator(Validator):
    def validate(self, document):
        is_a_directory = Path(document.text).is_dir()
        if not is_a_directory or len(document.text.strip()) == 0:
            raise ValidationError(
                message='Please enter a valid directory',
                cursor_position=len(document.text)
            )


def confirm_data_directory(directory: str, files: List[str]):
    stats = get_directory_stats(directory, files)
    is_accepted = ask(
        'confirm',
        f'Please confirm that you wish to upload {stats["numberOfFiles"]} files ({stats["sizeFriendly"]})',
        default=True
    )

    if not is_accepted:
        sys.exit(1)


def ask_process(processes: List[Process], input_value: str) -> str:
    process_names = [process.name for process in processes]
    return ask(
        'select',
        'What type of files?',
        default=input_value if input_value in process_names else None,
        choices=process_names
    )


def gather_upload_arguments(input_params: UploadArguments, projects: List[Project], processes: List[Process]):
    input_params['project'] = ask_project(projects, input_params.get('project'))

    input_params['data_directory'] = ask(
        'path',
        'Enter the full path of the data directory',
        required=True,
        validate=DataDirectoryValidator,
        default=input_params.get('data_directory') or '',
        complete_style=CompleteStyle.READLINE_LIKE,
        only_directories=True
    )

    upload_method = ask(
        'select',
        'What files would you like to upload?',
        choices=[
            Choice('Upload all files in directory', 'all'),
            Choice('Choose files from a list', 'select'),
            Choice('Specify a glob pattern', 'glob'),
        ]
    )
    input_params['files'] = get_files_in_directory(input_params['data_directory'])
    if upload_method == 'select':
        input_params['files'] = ask(
            'checkbox',
            'Select the files you wish to upload',
            choices=input_params['files']
        )
    elif upload_method == 'glob':
        matching_files = None
        while not matching_files:
            glob_pattern = ask('text', 'Glob pattern:')
            matching_files = [f for f in input_params['files'] if fnmatch(f, glob_pattern)]
            if len(matching_files) == 0:
                print('Glob pattern does not match any files, please specify another')

        input_params['files'] = matching_files

    confirm_data_directory(input_params['data_directory'], input_params['files'])

    input_params['process'] = ask_process(processes, input_params.get('process'))

    data_directory_name = Path(input_params['data_directory']).name
    default_name = input_params.get('name') or data_directory_name
    input_params['name'] = ask(
        'text',
        'What is the name of this dataset?',
        default=default_name,
        validate=lambda val: len(val.strip()) > 0 or 'Please enter a name'
    )
    input_params['description'] = ask(
        'text',
        'Enter a description of the dataset (optional)',
        default=input_params.get('description') or ''
    )

    return input_params
