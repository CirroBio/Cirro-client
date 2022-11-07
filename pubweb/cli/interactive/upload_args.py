import sys
from pathlib import Path
from typing import List

from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.validation import Validator, ValidationError

from pubweb.cli.interactive.common_args import ask_project, ask_use_third_party_tool
from pubweb.cli.interactive.utils import prompt_wrapper
from pubweb.cli.models import UploadArguments
from pubweb.file_utils import get_directory_stats
from pubweb.api.models.process import Process
from pubweb.api.models.project import Project


class DataDirectoryValidator(Validator):
    def validate(self, document):
        is_a_directory = Path(document.text).is_dir()
        if not is_a_directory or len(document.text.strip()) == 0:
            raise ValidationError(
                message='Please enter a valid directory',
                cursor_position=len(document.text)
            )


def ask_data_directory(input_value: str) -> str:
    directory_prompt = {
        'type': 'path',
        'name': 'data_directory',
        'message': 'Enter the full path of the data directory',
        'validate': DataDirectoryValidator,
        'default': input_value or '',
        'complete_style': CompleteStyle.READLINE_LIKE,
        'only_directories': True
    }

    answers = prompt_wrapper(directory_prompt)
    return answers['data_directory']


def confirm_data_directory(directory: str):
    stats = get_directory_stats(directory)
    answers = prompt_wrapper({
        'type': 'confirm',
        'message': f'Please confirm that you wish to upload {stats["numberOfFiles"]} files ({stats["sizeFriendly"]})',
        'name': 'continue',
        'default': True
    })

    if not answers['continue']:
        sys.exit(1)


def ask_name(input_value: str) -> str:
    name_prompt = {
        'type': 'input',
        'name': 'name',
        'message': 'What is the name of this dataset?',
        'validate': lambda val: len(val.strip()) > 0 or 'Please enter a name',
        'default': input_value or ''
    }

    answers = prompt_wrapper(name_prompt)
    return answers['name']


def ask_description(input_value: str) -> str:
    description_prompt = {
        'type': 'input',
        'name': 'description',
        'message': 'Enter a description of the dataset (optional)',
        'default': input_value or ''
    }

    answers = prompt_wrapper(description_prompt)
    return answers['description']


def ask_process(processes: List[Process], input_value: str) -> str:
    process_names = [process.name for process in processes]
    process_prompt = {
        'type': 'list',
        'name': 'process',
        'message': 'What type of files?',
        'choices': process_names,
        'default': input_value if input_value in process_names else None
    }
    answers = prompt_wrapper(process_prompt)
    return answers['process']


def gather_upload_arguments(input_params: UploadArguments, projects: List[Project], processes: List[Process]):
    input_params['project'] = ask_project(projects, input_params.get('project'))

    input_params['data_directory'] = ask_data_directory(input_params.get('data_directory'))
    confirm_data_directory(input_params['data_directory'])

    input_params['process'] = ask_process(processes, input_params.get('process'))

    data_directory_name = Path(input_params['data_directory']).name
    default_name = input_params.get('name') or data_directory_name
    input_params['name'] = ask_name(default_name)
    input_params['description'] = ask_description(input_params.get('description'))

    input_params['use_third_party_tool'] = ask_use_third_party_tool()
    return input_params
