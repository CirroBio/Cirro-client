from pubweb.cli.interactive import gather_upload_arguments, gather_download_arguments, gather_download_arguments_dataset, gather_login
from pubweb.auth import UsernameAndPasswordAuth
from pubweb.cli.models import UploadArguments, DownloadArguments
from pubweb.config import AuthConfig, save_config, load_config
from pubweb.file_utils import get_files_in_directory
from pubweb import PubWeb


def get_credentials():
    config = load_config()
    return config.username, config.password


def run_ingest(input_params: UploadArguments, interactive=False):
    pubweb = PubWeb(UsernameAndPasswordAuth(*get_credentials()))

    if interactive:
        projects = pubweb.project.list()
        processes = pubweb.process.list(process_type='INGEST')
        input_params = gather_upload_arguments(input_params, projects, processes)

    directory = input_params['data_directory']
    files = get_files_in_directory(directory)
    if len(files) == 0:
        raise RuntimeWarning("No files to upload, exiting")

    create_request = {
        'projectId': pubweb.project.get_project_id(input_params['project']),
        'processId': pubweb.process.get_process_id(input_params['process']),
        'name': input_params['name'],
        'description': input_params['description'],
        'files': files
    }

    create_resp = pubweb.dataset.create(create_request)
    pubweb.dataset.upload_files(dataset_id=create_resp['datasetId'],
                                project_id=create_request['projectId'],
                                directory=directory,
                                files=files)


def run_download(input_params: DownloadArguments, interactive=False):
    pubweb = PubWeb(UsernameAndPasswordAuth(*get_credentials()))

    if interactive:
        projects = pubweb.project.list()
        input_params = gather_download_arguments(input_params, projects)

        input_params['project'] = pubweb.project.get_project_id(input_params['project'])
        datasets = pubweb.dataset.find_by_project(input_params['project'])
        input_params = gather_download_arguments_dataset(input_params, datasets)

    dataset_params = {
        'project': pubweb.project.get_project_id(input_params['project']),
        'dataset': input_params['dataset']
    }

    pubweb.dataset.download_files(project_id=dataset_params['project'],
                                  dataset_id=dataset_params['dataset'],
                                  download_location=input_params['data_directory'])


def run_configure():
    username, password = gather_login()
    auth_config = AuthConfig(username, password)
    save_config(auth_config)
