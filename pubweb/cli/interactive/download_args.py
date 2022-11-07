from pathlib import Path
from typing import List
from fnmatch import fnmatch
from pubweb.cli.interactive.common_args import ask_project
from pubweb.cli.interactive.utils import prompt_wrapper, InputError
from pubweb.cli.models import DownloadArguments
from pubweb.api.models.dataset import Dataset
from pubweb.api.models.file import File
from pubweb.api.models.project import Project
from pubweb.utils import format_date


def ask_dataset(datasets: List[Dataset], input_value: str) -> str:
    if len(datasets) == 0:
        raise RuntimeWarning("No datasets available")
    sorted_datasets = sorted(datasets, key=lambda d: d.created_at, reverse=True)
    dataset_prompt = {
        'type': 'autocomplete',
        'name': 'dataset',
        'message': 'What dataset would you like to download? (Press Tab to see all options)',
        'choices': [f'{dataset.name} - {dataset.id}' for dataset in sorted_datasets],
        'meta_information': {
            f'{dataset.name} - {dataset.id}': f'{format_date(dataset.created_at)}'
            for dataset in datasets
        },
        'ignore_case': True
    }
    answers = prompt_wrapper(dataset_prompt)
    choice = answers['dataset']
    # Map the answer to a dataset
    for dataset in datasets:
        if f'{dataset.name} - {dataset.id}' == choice:
            return dataset.id
    raise InputError("User must select a dataset to download")


def ask_dataset_files(input_params: DownloadArguments, files: List[File]) -> List[File]:
    """Get the list of files which the user would like to download from the dataset."""

    choices = [
        "Download all files",
        "Select files from a list",
        "Select files with a naming pattern (glob)"
    ]

    selection_mode_prompt = {
        'type': 'select',
        'name': 'mode',
        'message': 'Which files would you like to download from this dataset?',
        'choices': choices
    }

    answers = prompt_wrapper(selection_mode_prompt)

    if answers['mode'] == choices[0]:
        return files
    elif answers['mode'] == choices[1]:
        return ask_dataset_files_list(files)
    else:
        return ask_dataset_files_glob(files)


def ask_dataset_files_list(files: List[File]) -> List[File]:
    answers = prompt_wrapper({
        'type': 'checkbox',
        'name': 'files',
        'message': 'Select the files to download',
        'choices': [
            file.relative_path
            for file in files
        ]
    })

    return [
        file
        for file in files
        if file.relative_path in set(answers['files'])
    ]


def ask_dataset_files_glob(files: List[File]) -> List[File]:

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


def ask_dataset_files_glob_single(files: List[File]) -> List[File]:

    print("All Files:")
    for file in files:
        print(f" - {file.relative_path}")

    answers = prompt_wrapper({
        'type': 'text',
        'name': 'glob',
        'message': 'Select files by naming pattern (using the * wildcard)',
        'default': '*'
    })

    selected_files = [
        file
        for file in files
        if fnmatch(file.relative_path, answers['glob'])
    ]

    print("Selected Files:")
    for file in selected_files:
        print(f" - {file.relative_path}")

    return selected_files


def ask_directory(input_value: str) -> str:
    directory_prompt = {
        'type': 'path',
        'name': 'directory',
        'only_directories': True,
        'message': 'Where would you like to download these files?',
        'default': input_value or str(Path.cwd())
    }

    answers = prompt_wrapper(directory_prompt)
    return answers['directory']


def gather_download_arguments(input_params: DownloadArguments, projects: List[Project]):
    input_params['project'] = ask_project(projects, input_params.get('project'))
    return input_params


def gather_download_arguments_dataset(input_params: DownloadArguments, datasets: List[Dataset]):
    input_params['dataset'] = ask_dataset(datasets, input_params.get('dataset'))
    input_params['data_directory'] = ask_directory(input_params.get('data_directory'))
    return input_params


def gather_download_arguments_dataset_files(input_params: DownloadArguments, files: List[File]):
    input_params['files'] = ask_dataset_files(input_params, files)
    return input_params
