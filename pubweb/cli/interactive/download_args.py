from pathlib import Path
from typing import List

from pubweb.cli.interactive.common_args import ask_project
from pubweb.cli.interactive.prompt_wrapper import prompt_wrapper
from pubweb.cli.models import DownloadArguments


def ask_dataset(datasets, input_value):
    if len(datasets) == 0:
        raise RuntimeWarning("No datasets available")

    dataset_prompt = {
        'type': 'list',
        'name': 'dataset',
        'message': 'What dataset would you like to download?',
        'choices': [f'{dataset["name"]} ({dataset["id"]})' for dataset in datasets]
    }
    answers = prompt_wrapper(dataset_prompt)
    choice = answers['dataset']
    return next(dataset for dataset in datasets if f'{dataset["name"]} ({dataset["id"]})' == choice)['id']


def ask_directory(input_value):
    directory_prompt = {
        'type': 'path',
        'name': 'directory',
        'only_directories': True,
        'message': 'Where would you like to download these files?',
        'default': input_value or str(Path.cwd())
    }

    answers = prompt_wrapper(directory_prompt)
    return answers['directory']


def gather_download_arguments(input_params: DownloadArguments, projects: List):
    input_params['data_directory'] = ask_directory(input_params.get('data_directory'))
    input_params['project'] = ask_project(projects, input_params.get('project'))
    return input_params


def gather_download_arguments_dataset(input_params: DownloadArguments, datasets: List):
    input_params['dataset'] = ask_dataset(datasets, input_params.get('dataset'))
    return input_params
