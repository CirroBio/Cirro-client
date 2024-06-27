import logging
import sys

import pandas as pd
from cirro_api_client.v1.models import UploadDatasetRequest, Status, Executor

from cirro.cirro_client import CirroApi
from cirro.cli.interactive.auth_args import gather_auth_config
from cirro.cli.interactive.download_args import gather_download_arguments, ask_dataset_files
from cirro.cli.interactive.download_args import gather_download_arguments_dataset
from cirro.cli.interactive.list_dataset_args import gather_list_arguments
from cirro.cli.interactive.upload_args import gather_upload_arguments
from cirro.cli.interactive.utils import get_id_from_name, get_item_from_name_or_id, InputError
from cirro.cli.models import ListArguments, UploadArguments, DownloadArguments
from cirro.config import UserConfig, save_user_config, load_user_config
from cirro.file_utils import get_files_in_directory

NO_PROJECTS = "No projects available"
# Log to STDOUT
log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)-8s [Cirro CLI] %(message)s'
)
logger = logging.getLogger("CLI")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)


def run_list_datasets(input_params: ListArguments, interactive=False):
    """List the datasets available in a particular project."""
    _check_configure()
    cirro = CirroApi()
    logger.info(f"Collecting data from {cirro.configuration.base_url}")

    # If the user provided the --interactive flag
    if interactive:

        # Get the list of projects available to the user
        projects = cirro.projects.list()

        if len(projects) == 0:
            raise InputError(NO_PROJECTS)

        # Prompt the user for the project
        input_params = gather_list_arguments(input_params, projects)

    # List the datasets available in that project
    datasets = cirro.datasets.list(input_params['project'])

    sorted_datasets = sorted(datasets, key=lambda d: d.created_at, reverse=True)
    df = pd.DataFrame.from_records([d.to_dict() for d in sorted_datasets])
    df = df[['id', 'name', 'description', 'processId', 'status', 'createdBy', 'createdAt']]
    print(df.to_string())


def run_ingest(input_params: UploadArguments, interactive=False):
    _check_configure()
    cirro = CirroApi()
    logger.info(f"Collecting data from {cirro.configuration.base_url}")
    processes = cirro.processes.list(process_type=Executor.INGEST)

    logger.info("Listing available projects")
    projects = cirro.projects.list()

    if len(projects) == 0:
        raise InputError(NO_PROJECTS)

    if interactive:
        input_params, files = gather_upload_arguments(input_params, projects, processes)
        directory = input_params['data_directory']
    else:
        directory = input_params['data_directory']
        files = get_files_in_directory(directory)

    if len(files) == 0:
        raise InputError("No files to upload")

    process = get_item_from_name_or_id(processes, input_params['process'])
    logger.info(f"Validating expected files: {process.name}")
    try:
        cirro.processes.check_dataset_files(process_id=process.id, files=files, directory=directory)
    except ValueError as e:
        raise InputError(e)
    logger.info("Creating new dataset")

    upload_dataset_request = UploadDatasetRequest(
        process_id=process.id,
        name=input_params['name'],
        description=input_params['description'],
        expected_files=files
    )

    project_id = get_id_from_name(projects, input_params['project'])
    create_resp = cirro.datasets.create(project_id=project_id,
                                        upload_request=upload_dataset_request)

    logger.info("Uploading files")
    cirro.datasets.upload_files(project_id=project_id,
                                dataset_id=create_resp.id,
                                directory=directory,
                                files=files)

    if cirro.configuration.enable_additional_checksum:
        checksum_method = "SHA256"
    else:
        checksum_method = "MD5"
    logger.info(f"File content validated by {checksum_method}")


def run_download(input_params: DownloadArguments, interactive=False):
    _check_configure()
    cirro = CirroApi()
    logger.info(f"Collecting data from {cirro.configuration.base_url}")

    logger.info("Listing available projects")
    projects = cirro.projects.list()

    if len(projects) == 0:
        raise InputError(NO_PROJECTS)

    files_to_download = None
    if interactive:
        input_params = gather_download_arguments(input_params, projects)

        input_params['project'] = get_id_from_name(projects, input_params['project'])
        datasets = cirro.datasets.list(input_params['project'])
        # Filter out datasets that are not complete
        datasets = [d for d in datasets if d.status == Status.COMPLETED]
        input_params = gather_download_arguments_dataset(input_params, datasets)
        files = cirro.datasets.get_file_listing(input_params['project'], input_params['dataset'])

        if len(files) == 0:
            raise InputError('There are no files in this dataset to download')

        files_to_download = ask_dataset_files(files)

    logger.info("Downloading files")
    if cirro.configuration.enable_additional_checksum:
        checksum_method = "SHA256"
    else:
        checksum_method = "MD5"
    logger.info(f"File content validated by {checksum_method}")

    project_id = get_id_from_name(projects, input_params['project'])
    dataset_id = input_params['dataset']
    cirro.datasets.download_files(project_id=project_id,
                                  dataset_id=dataset_id,
                                  download_location=input_params['data_directory'],
                                  files=files_to_download)


def run_configure():
    auth_method, base_url, auth_method_config, enable_additional_checksum = gather_auth_config()
    save_user_config(UserConfig(auth_method=auth_method,
                                auth_method_config=auth_method_config,
                                base_url=base_url,
                                transfer_max_retries=None,
                                enable_additional_checksum=enable_additional_checksum))


def _check_configure():
    """
    Prompts the user to do initial configuration if needed
    """
    config = load_user_config()
    if config is None:
        run_configure()
        return

    # Legacy check for old config
    if config.base_url == 'cirro.bio':
        run_configure()


def handle_error(e: Exception):
    logger.error(e)
    sys.exit(1)
