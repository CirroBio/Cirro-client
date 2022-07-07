from pathlib import Path
from typing import List

from pubweb.cli.interactive.common_args import ask_project
from pubweb.cli.interactive.utils import ask
from pubweb.cli.models import DownloadArguments
from pubweb.models.dataset import Dataset
from pubweb.models.project import Project
from pubweb.utils import format_date


def ask_dataset(datasets: List[Dataset], input_value: str) -> str:
    if len(datasets) == 0:
        raise RuntimeWarning("No datasets available")
    sorted_datasets = sorted(datasets, key=lambda d: d.created_at, reverse=True)
    default_dataset = None
    if input_value:
        matched_dataset = next((d for d in datasets
                                if d.name == input_value or d.id == input_value), None)
        if matched_dataset is not None:
            default_dataset = matched_dataset

    dataset_choice = ask('autocomplete',
                         'What dataset would you like to download? (Press Tab to see all options)',
                         choices=[f'{dataset.name} - {dataset.id}' for dataset in sorted_datasets],
                         default=f'{default_dataset.name} - {default_dataset.id}',
                         meta_information={
                             f'{dataset.name} - {dataset.id}': f'{format_date(dataset.created_at)}'
                             for dataset in datasets
                         },
                         ignore_case=True)

    return next(dataset for dataset in datasets if f'{dataset.name} - {dataset.id}' == dataset_choice).id


def gather_download_arguments(input_params: DownloadArguments, projects: List[Project]):
    input_params['project'] = ask_project(projects, input_params.get('project'))
    return input_params


def gather_download_arguments_dataset(input_params: DownloadArguments, datasets: List[Dataset]):
    input_params['dataset'] = ask_dataset(datasets, input_params.get('dataset'))
    input_params['data_directory'] = ask('path',
                                         'Where would you like to download these files?',
                                         default=input_params.get('data_directory') or str(Path.cwd()),
                                         only_directories=True)
    return input_params
