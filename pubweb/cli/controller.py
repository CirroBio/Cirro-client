import os

from pubweb.cli.arguments import gather_arguments, gather_download_arguments, gather_login
from pubweb.clients import create_clients
from pubweb.dataset import Dataset
from pubweb.file_utils import get_files_in_directory


def get_credentials(interactive):
    username = os.environ.get('PW_USERNAME')
    password = os.environ.get('PW_PASSWORD')
    if not username or not password:
        if interactive:
            username, password = gather_login()
        else:
            raise RuntimeWarning('Please set the PW_USERNAME and PW_PASSWORD environment variables to log in')
    return username, password


def run_ingest(input_params, interactive=False):
    data_client, rest_client = create_clients(*get_credentials(interactive))

    if interactive:
        input_params = gather_arguments(data_client, input_params)

    directory = input_params['data_directory']
    files = get_files_in_directory(directory)
    if len(files) == 0:
        raise RuntimeWarning("No files to upload, exiting")

    create_params = {
        'project': data_client.get_project_id(input_params['project']),
        'process': data_client.get_process_id(input_params['process']),
        'name': input_params['name'],
        'desc': input_params['description'],
        'files': [{'name': file_name} for file_name in files]
    }

    dataset = Dataset(rest_client)
    dataset.create(create_params)
    dataset.upload_directory(directory)


def run_download(input_params, interactive=False):
    data_client, rest_client = create_clients(*get_credentials(interactive))

    if interactive:
        input_params = gather_download_arguments(data_client, input_params)

    dataset_params = {
        'project': data_client.get_project_id(input_params['project']),
        'dataset': input_params['dataset']
    }

    dataset = Dataset(rest_client, dataset_params)
    dataset.download_files(input_params['data_directory'])
