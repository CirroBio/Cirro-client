import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import List
from fnmatch import fnmatch

from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.validation import Validator, ValidationError
from questionary import Choice

from cirro.api.models.process import Process
from cirro.api.models.project import Project
from cirro.cli.interactive.common_args import ask_project
from cirro.cli.interactive.utils import ask, prompt_wrapper
from cirro.cli.models import UploadArguments
from cirro.file_utils import get_files_in_directory, get_files_stats


class DataDirectoryValidator(Validator):
    def validate(self, document):
        is_a_directory = Path(document.text).is_dir()
        if not is_a_directory or len(document.text.strip()) == 0:
            raise ValidationError(
                message='Please enter a valid directory',
                cursor_position=len(document.text)
            )


def confirm_data_files(data_directory: str, files: List[str]):
    stats = get_files_stats([
        Path(data_directory) / file
        for file in files
    ])
    answers = prompt_wrapper({
        'type': 'confirm',
        'message': f'Please confirm that you wish to upload {stats["numberOfFiles"]} files ({stats["sizeFriendly"]})',
        'name': 'continue',
        'default': True
    })

    if not answers['continue']:
        sys.exit(1)


def ask_process(processes: List[Process], input_value: str) -> str:
    process_names = [process.name for process in processes]
    process_names.sort()
    return ask(
        'select',
        'What type of files?',
        default=input_value if input_value in process_names else None,
        choices=process_names
    )


def ask_include_hidden() -> bool:
    return prompt_wrapper({
        'type': 'confirm',
        'message': "Include hidden files (expert: e.g. Zarr)",
        'name': 'include_hidden',
        'default': False
    })['include_hidden']


def ask_files_in_directory(data_directory) -> List[str]:

    # Ask whether hidden files should be included
    include_hidden = ask_include_hidden()

    # Get the list of all files in the directory
    # (relative to the data_directory)
    files = get_files_in_directory(
        data_directory,
        include_hidden=include_hidden
    )

    choices = [
        "Upload all files",
        "Select files from a list",
        "Select files with a naming pattern (glob)"
    ]

    selection_mode_prompt = {
        'type': 'select',
        'name': 'mode',
        'message': 'Which files would you like to upload from this dataset?',
        'choices': choices
    }

    answers = prompt_wrapper(selection_mode_prompt)

    if answers['mode'] == choices[0]:
        return files
    elif answers['mode'] == choices[1]:
        return ask_dataset_files_list(files)
    else:
        return ask_dataset_files_glob(files)


def ask_dataset_files_list(files: List[str]) -> List[str]:
    return prompt_wrapper({
        'type': 'checkbox',
        'name': 'files',
        'message': 'Select the files to upload',
        'choices': files
    })['files']


def ask_dataset_files_glob(files: List[str]) -> List[str]:

    selected_files = ask_dataset_files_glob_single(files)
    answers = prompt_wrapper({
        'type': 'confirm',
        'name': 'confirm',
        'message': f'Number of files selected: {len(selected_files):} / {len(files):,}'
    })
    while not answers['confirm']:
        selected_files = ask_dataset_files_glob_single(files)
        answers = prompt_wrapper({
            'type': 'confirm',
            'name': 'confirm',
            'message': f'Number of files selected: {len(selected_files):} / {len(files):,}'
        })
    return selected_files


def ask_dataset_files_glob_single(files: List[str]) -> List[str]:

    print("All Files:")
    for file in files:
        print(f" - {file}")

    answers = prompt_wrapper({
        'type': 'text',
        'name': 'glob',
        'message': 'Select files by naming pattern (using the * wildcard)',
        'default': '*'
    })

    selected_files = [
        file
        for file in files
        if fnmatch(file, answers['glob'])
    ]

    print("Selected Files:")
    for file in selected_files:
        print(f" - {file}")

    return selected_files


def gather_upload_arguments(input_params: UploadArguments, projects: List[Project], processes: List[Process]):
    input_params['project'] = ask_project(projects, input_params.get('project'))

    input_params['data_directory'] = ask_data_directory(input_params.get('data_directory'))
    files = ask_files_in_directory(input_params['data_directory'])

    confirm_data_files(input_params['data_directory'], files)

    input_params['process'] = ask_process(processes, input_params.get('process'))

    data_directory_name = Path(input_params['data_directory']).name
    default_name = input_params.get('name') or data_directory_name
    input_params['name'] = ask_name(default_name)
    input_params['description'] = ask_description(input_params.get('description'))
    return input_params, files
