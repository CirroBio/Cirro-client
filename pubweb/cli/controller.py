import os
import sys

from pubweb.auth import CognitoAuthInfo
from pubweb.cli.arguments import gather_arguments, gather_login
from pubweb.data_client import DataClient
from pubweb.dataset import Dataset
from pubweb.file_utils import get_files_in_directory
from pubweb.rest_client import RestClient


def run_ingest(input_params, interactive=False):
    username = os.environ.get('PW_USERNAME')
    password = os.environ.get('PW_PASSWORD')
    if not username or not password:
        if interactive:
            username, password = gather_login()
        else:
            print('Please set the PW_USERNAME and PW_PASSWORD environment variables to log in')
            sys.exit(1)

    auth_info = CognitoAuthInfo(username, password)
    data_client = DataClient(auth_info.get_request_auth())
    rest_client = RestClient(auth_info.get_request_auth())
    if interactive:
        input_params = gather_arguments(data_client, input_params)
    directory = input_params['data_directory']

    files = get_files_in_directory(directory)
    if len(files) == 0:
        print("No files to upload, exiting")
        sys.exit(1)

    create_params = {
        'project': data_client.get_project_id(input_params['project']),
        'process': data_client.get_process_id(input_params['process']),
        'name': input_params['name'],
        'desc': input_params['description'],
        'files': [{'name': file_name} for file_name in files]
    }

    dataset = Dataset(create_params, rest_client)
    dataset.create()
    dataset.upload_directory(directory)
