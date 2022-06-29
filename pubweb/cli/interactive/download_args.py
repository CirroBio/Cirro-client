from pathlib import Path
from typing import List

from pubweb.cli.interactive.common_args import ask_project
from pubweb.cli.interactive.utils import prompt_wrapper
from pubweb.cli.models import DownloadArguments
from pubweb.utils import parse_json_date, format_date


def ask_dataset(datasets, input_value):
    if len(datasets) == 0:
        raise RuntimeWarning("No datasets available")
    sorted_datasets = sorted(datasets, key=lambda d: parse_json_date(d["createdAt"]), reverse=True)
    dataset_prompt = {
        'type': 'autocomplete',
        'name': 'dataset',
        'message': 'What dataset would you like to download? (Press Tab to see all options)',
        'choices': [f'{dataset["name"]} - {dataset["id"]}' for dataset in sorted_datasets],
        'meta_information': {
            f'{dataset["name"]} - {dataset["id"]}': f'{format_date(dataset["createdAt"])}'
            for dataset in datasets
        },
        'ignore_case': True
    }
    answers = prompt_wrapper(dataset_prompt)
    choice = answers['dataset']
    return next(dataset for dataset in datasets if f'{dataset["name"]} - {dataset["id"]}' == choice)['id']


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
    input_params['project'] = ask_project(projects, input_params.get('project'))
    return input_params


def gather_download_arguments_dataset(input_params: DownloadArguments, datasets: List):
    input_params['dataset'] = ask_dataset(datasets, input_params.get('dataset'))
    input_params['data_directory'] = ask_directory(input_params.get('data_directory'))
    return input_params
