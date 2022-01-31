import os
import sys
from pathlib import Path
from typing import Dict

from PyInquirer import prompt, Validator
from prompt_toolkit.terminal.win32_output import NoConsoleScreenBufferError
from prompt_toolkit.validation import ValidationError

from pubweb.clients.data import DataClient
from pubweb.file_utils import get_directory_stats


class DataDirectoryValidator(Validator):
    def validate(self, document):
        is_a_directory = Path(document.text).is_dir()
        if not is_a_directory or len(document.text.strip()) == 0:
            raise ValidationError(
                message='Please enter a valid directory',
                cursor_position=len(document.text)
            )


def ask_project(projects, input_value):
    project_prompt = {
        'type': 'list',
        'name': 'project',
        'message': 'What project is this dataset associated with?',
        'choices': [project["name"] for project in projects],
        'default': input_value or ''
    }
    answers = prompt(project_prompt)
    return answers['project']


def ask_dataset(datasets, input_value):
    if len(datasets) == 0:
        raise RuntimeWarning("No datasets available")

    dataset_prompt = {
        'type': 'list',
        'name': 'dataset',
        'message': 'What dataset would you like to download?',
        'choices': [f'{dataset["name"]} ({dataset["id"]})' for dataset in datasets],
        'default': input_value or ''
    }
    answers = prompt(dataset_prompt)
    choice = answers['dataset']
    return next(dataset for dataset in datasets if f'{dataset["name"]} ({dataset["id"]})' == choice)['id']


def ask_data_directory(input_value):
    directory_prompt = {
        'type': 'input',
        'name': 'data_directory',
        'message': 'Enter the full path of the data directory',
        'validate': DataDirectoryValidator,
        'default': input_value or ''
    }

    answers = prompt(directory_prompt)
    return answers['data_directory']


def confirm_data_directory(directory):
    stats = get_directory_stats(directory)
    answers = prompt({
        'type': 'confirm',
        'message': f'Please confirm that you wish to upload {stats["numberOfFiles"]} files ({stats["size"]})',
        'name': 'continue',
        'default': True
    })

    if not answers['continue']:
        sys.exit(1)


def ask_name(input_value):
    name_prompt = {
        'type': 'input',
        'name': 'name',
        'message': 'What is the name of this dataset?',
        'validate': lambda val: len(val.strip()) > 0 or 'Please enter a name',
        'default': input_value or ''
    }

    answers = prompt(name_prompt)
    return answers['name']


def ask_description(input_value):
    description_prompt = {
        'type': 'input',
        'name': 'description',
        'message': 'Enter a description of the dataset (optional)',
        'default': input_value or ''
    }

    answers = prompt(description_prompt)
    return answers['description']


def ask_process(processes, input_value):
    process_prompt = {
        'type': 'list',
        'name': 'process',
        'message': 'What type of files?',
        'choices': [process['name'] for process in processes],
        'default': input_value or ''
    }
    answers = prompt(process_prompt)
    return answers['process']


def gather_arguments(data_client: DataClient, input_params: Dict):
    try:
        input_params['data_directory'] = ask_data_directory(input_params.get('data_directory'))
        confirm_data_directory(input_params['data_directory'])

        processes = data_client.get_ingest_processes()
        input_params['process'] = ask_process(processes, input_params.get('process'))

        projects = data_client.get_projects_list()
        input_params['project'] = ask_project(projects, input_params.get('project'))

        data_directory_name = Path(input_params['data_directory']).name
        default_name = input_params.get('name') or data_directory_name
        input_params['name'] = ask_name(default_name)
        input_params['description'] = ask_description(input_params.get('description'))

        return input_params
    except NoConsoleScreenBufferError:
        pass


def gather_download_arguments(data_client: DataClient, input_params: Dict):
    try:

        projects = data_client.get_projects_list()
        input_params['project'] = ask_project(projects, input_params.get('project'))

        input_params['project'] = data_client.get_project_id(input_params['project'])
        datasets = data_client.get_datasets_list(input_params['project'])
        input_params['dataset'] = ask_dataset(datasets, input_params.get('dataset'))

        input_params['data_directory'] = ask_data_directory(input_params.get('data_directory'))

        return input_params
    except NoConsoleScreenBufferError:
        pass


def gather_login():
    answers = prompt([
        {
            'type': 'input',
            'name': 'username',
            'message': 'Username',
            'default': os.environ.get('PW_USERNAME') or ''
        },
        {
            'type': 'password',
            'name': 'password',
            'message': 'Password'
        }
    ])
    return answers['username'], answers['password']
