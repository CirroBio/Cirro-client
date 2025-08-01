import importlib.metadata
import json
import logging
import os
import sys
from pathlib import Path

import requests
from cirro_api_client.v1.models import UploadDatasetRequest, Status, Executor

from cirro.cirro_client import CirroApi
from cirro.cli.interactive.auth_args import gather_auth_config
from cirro.cli.interactive.create_pipeline_config import gather_create_pipeline_config_arguments
from cirro.cli.interactive.download_args import gather_download_arguments, ask_dataset_files
from cirro.cli.interactive.download_args import gather_download_arguments_dataset
from cirro.cli.interactive.list_dataset_args import gather_list_arguments
from cirro.cli.interactive.upload_args import gather_upload_arguments
from cirro.cli.interactive.upload_reference_args import gather_reference_upload_arguments
from cirro.cli.interactive.utils import get_id_from_name, get_item_from_name_or_id, InputError
from cirro.cli.models import ListArguments, UploadArguments, DownloadArguments, CreatePipelineConfigArguments, \
    UploadReferenceArguments
from cirro.config import UserConfig, save_user_config, load_user_config
from cirro.file_utils import get_files_in_directory
from cirro.models.process import PipelineDefinition, ConfigAppStatus, CONFIG_APP_URL
from cirro.services.service_helpers import list_all_datasets

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
    _check_version()
    cirro = CirroApi()
    logger.info(f"Collecting data from {cirro.configuration.base_url}")
    projects = cirro.projects.list()

    if len(projects) == 0:
        raise InputError(NO_PROJECTS)

    if interactive:
        # Prompt the user for the project
        input_params = gather_list_arguments(input_params, projects)
    else:
        input_params['project'] = get_id_from_name(projects, input_params['project'])

    # List the datasets available in that project
    datasets = cirro.datasets.list(input_params['project'])

    sorted_datasets = sorted(datasets, key=lambda d: d.created_at, reverse=True)

    import pandas as pd
    df = pd.DataFrame.from_records([d.to_dict() for d in sorted_datasets])
    df = df[['id', 'name', 'description', 'processId', 'status', 'createdBy', 'createdAt']]
    print(df.to_string())


def run_ingest(input_params: UploadArguments, interactive=False):
    _check_configure()
    _check_version()
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
        input_params['project'] = get_id_from_name(projects, input_params['project'])
        input_params['process'] = get_id_from_name(processes, input_params['process'])
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
    logger.info(f"File content validated by {cirro.configuration.checksum_method_display}")


def run_download(input_params: DownloadArguments, interactive=False):
    _check_configure()
    _check_version()
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
        datasets = list_all_datasets(project_id=input_params['project'], client=cirro)
        # Filter out datasets that are not complete
        datasets = [d for d in datasets if d.status == Status.COMPLETED]
        input_params = gather_download_arguments_dataset(input_params, datasets)
        files = cirro.datasets.get_assets_listing(input_params['project'], input_params['dataset']).files

        if len(files) == 0:
            raise InputError('There are no files in this dataset to download')

        files_to_download = ask_dataset_files(files)
        project_id = input_params['project']
        dataset_id = input_params['dataset']

    else:
        project_id = get_id_from_name(projects, input_params['project'])
        datasets = cirro.datasets.list(project_id)
        dataset_id = get_id_from_name(datasets, input_params['dataset'])

        if input_params['file']:
            all_files = cirro.datasets.get_assets_listing(project_id, dataset_id).files
            files_to_download = []

            for filepath in input_params['file']:
                if not filepath.startswith('data/'):
                    filepath = os.path.join('data/', filepath)
                file = next((f for f in all_files if f.relative_path == filepath), None)
                if not file:
                    logger.warning(f"Could not find file {filepath}. Skipping.")
                    continue
                files_to_download.append(file)

    logger.info("Downloading files")
    logger.info(f"File content validated by {cirro.configuration.checksum_method_display}")

    cirro.datasets.download_files(project_id=project_id,
                                  dataset_id=dataset_id,
                                  download_location=input_params['data_directory'],
                                  files=files_to_download)


def run_upload_reference(input_params: UploadReferenceArguments, interactive=False):
    _check_configure()
    _check_version()
    cirro = CirroApi()
    logger.info(f"Collecting data from {cirro.configuration.base_url}")

    reference_types = cirro.references.get_types()
    projects = cirro.projects.list()

    if len(projects) == 0:
        raise InputError(NO_PROJECTS)

    if interactive:
        input_params, files = gather_reference_upload_arguments(input_params, projects, reference_types)
    else:
        files = [Path(f) for f in input_params['reference_file']]

    project_id = get_id_from_name(projects, input_params['project'])
    reference_type = next((rt for rt in reference_types if rt.name == input_params['reference_type']), None)

    cirro.references.upload_reference(project_id=project_id,
                                      ref_type=reference_type,
                                      name=input_params['name'],
                                      reference_files=files)


def run_configure():
    _check_version()
    auth_method, base_url, auth_method_config, enable_additional_checksum = gather_auth_config()
    save_user_config(UserConfig(auth_method=auth_method,
                                auth_method_config=auth_method_config,
                                base_url=base_url,
                                transfer_max_retries=None,
                                enable_additional_checksum=enable_additional_checksum))


def run_create_pipeline_config(input_params: CreatePipelineConfigArguments, interactive=False):
    """
    Creates the pipeline configuration files for the CLI.
    This is a placeholder function that can be expanded in the future.
    """
    _check_version()
    logger.info("Creating pipeline configuration files...")

    if interactive:
        input_params = gather_create_pipeline_config_arguments(input_params)
    else:
        if not input_params['pipeline_dir']:
            raise InputError("Root directory is required")
        if not os.path.isdir(input_params['pipeline_dir']):
            raise InputError(f"Root directory {input_params['pipeline_dir']} does not exist")

    logger.debug(input_params)
    pipeline_definition = PipelineDefinition(
        root_dir=input_params['pipeline_dir'],
        entrypoint=input_params.get('entrypoint'),
        logger=logger
    )

    output_dir = input_params.get('output_dir')
    output_paths = {filename: os.path.join(output_dir, filename)  # type: ignore
                    for filename in ['process-form.json', 'process-input.json']}

    logger.info(f"Writing pipeline configuration files to {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    with open(output_paths['process-form.json'], 'w') as f:
        logger.info(f"Writing form configuration to {output_paths['process-form.json']}")
        json.dump(pipeline_definition.form_configuration, f, indent=2)

    with open(output_paths['process-input.json'], 'w') as f:
        logger.info(f"Writing input configuration to {output_paths['process-input.json']}")
        json.dump(pipeline_definition.input_configuration, f, indent=2)

    logger.info("Pipeline configuration files created successfully.")

    if pipeline_definition.config_app_status == ConfigAppStatus.RECOMMENDED:
        logger.warning(
            "It is recommended that you verify your pipeline configuration "
            "using the Cirro Pipeline Configuration App for this pipeline:\n"
            f"{CONFIG_APP_URL}")


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


def _check_version():
    """
    Prompts the user to update their package version if needed
    """
    yellow_color = '\033[93m'
    reset_color = '\033[0m'

    try:
        current_version = importlib.metadata.version('cirro')
        response = requests.get("https://pypi.org/pypi/cirro/json")
        response.raise_for_status()
        latest_version = response.json()["info"]["version"]

        if current_version != latest_version:
            print(f"{yellow_color}Warning:{reset_color} Cirro version {current_version} "
                  f"is out of date. Update to {latest_version} with 'pip install cirro --upgrade'.")

    except Exception:
        return


def handle_error(e: Exception):
    logger.error(f"{e.__class__.__name__}: {e}")
    sys.exit(1)
