from pubweb.auth import CognitoAuthInfo
from pubweb.cli.arguments import gather_arguments
from pubweb.data_client import DataClient
from pubweb.dataset.manifest import get_files_in_directory


def run_ingest(input_params, interactive=False):
    auth_info = CognitoAuthInfo(None, None)
    data_client = DataClient(auth_info.get_request_auth())
    if interactive:
        input_params = gather_arguments(data_client, input_params)

    files = get_files_in_directory(input_params['data_directory'])

    print(files)

    print(input_params)

    # dataset = Dataset()
    # dataset.create()
    # dataset.upload_directory(directory)
