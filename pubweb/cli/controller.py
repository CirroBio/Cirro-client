import sys

from pubweb.auth import CognitoAuthInfo
from pubweb.cli.arguments import gather_arguments
from pubweb.data_client import DataClient

from pubweb.dataset import Dataset
from pubweb.file_utils import get_files_in_directory
from pubweb.rest_client import RestClient


def run_ingest(input_params, interactive=False):
    auth_info = CognitoAuthInfo(None, None)
    data_client = DataClient(auth_info.get_request_auth())
    rest_client = RestClient(auth_info.get_request_auth())
    if interactive:
        input_params = gather_arguments(data_client, input_params)
    directory = input_params['data_directory']
    files = get_files_in_directory(directory)
    if len(files) == 0:
        print("No files to upload, exiting")
        sys.exit(1)
    print(files)

    print(input_params)

    dataset = Dataset(input_params, rest_client)
    dataset.create()
    dataset.upload_directory(directory)
