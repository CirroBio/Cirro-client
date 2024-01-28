import pandas as pd
from cirro_api_client.v1.models import Executor, UploadDatasetRequest

from cirro.cirro_client import Cirro
from cirro.cli.interactive.auth_args import gather_auth_config
from cirro.cli.interactive.download_args import gather_download_arguments, ask_dataset_files
from cirro.cli.interactive.download_args import gather_download_arguments_dataset
from cirro.cli.interactive.list_dataset_args import gather_list_arguments
from cirro.cli.interactive.upload_args import gather_upload_arguments
from cirro.cli.interactive.utils import get_id_from_name, get_item_from_name_or_id
from cirro.cli.interactive.workflow_args import get_preprocess_script, get_additional_inputs, get_outputs, \
    get_child_processes, \
    get_repository, get_description, get_output_resources_path
from cirro.cli.interactive.workflow_form_args import prompt_user_inputs, get_nextflow_schema, convert_nf_schema
from cirro.cli.models import ListArguments, UploadArguments, DownloadArguments
from cirro.config import UserConfig, save_user_config, load_user_config
from cirro.file_utils import get_files_in_directory
from cirro.helpers import WorkflowConfigBuilder

NO_PROJECTS = "No projects available"


def run_list_datasets(input_params: ListArguments, interactive=False):
    """List the datasets available in a particular project."""
    _check_configure()
    cirro = Cirro()

    # If the user provided the --interactive flag
    if interactive:

        # Get the list of projects available to the user
        projects = cirro.projects.list()

        if len(projects) == 0:
            print(NO_PROJECTS)
            return

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
    cirro = Cirro()
    projects = cirro.projects.list()
    processes = cirro.processes.list()

    if len(projects) == 0:
        print(NO_PROJECTS)
        return

    if interactive:
        input_params, files = gather_upload_arguments(input_params, projects, processes)
        directory = input_params['data_directory']
    else:
        directory = input_params['data_directory']
        files = get_files_in_directory(directory)

    if len(files) == 0:
        raise RuntimeWarning("No files to upload, exiting")

    process = get_item_from_name_or_id(processes, input_params['process'])
    cirro.processes.check_dataset_files(process_id=process.id, files=files, directory=directory)

    upload_dataset_request = UploadDatasetRequest(
        process_id=process.id,
        name=input_params['name'],
        description=input_params['description'],
        expectedFiles=files
    )

    project_id = get_id_from_name(projects, input_params['project'])
    create_resp = cirro.datasets.create(project_id=project_id,
                                        upload_request=upload_dataset_request)

    cirro.datasets.upload_files(project_id=project_id,
                                dataset_id=create_resp.id,
                                local_directory=directory,
                                files=files)


def run_download(input_params: DownloadArguments, interactive=False):
    _check_configure()
    cirro = Cirro()

    projects = cirro.projects.list()

    if len(projects) == 0:
        print(NO_PROJECTS)
        return

    files_to_download = None
    if interactive:
        input_params = gather_download_arguments(input_params, projects)

        input_params['project'] = get_id_from_name(projects, input_params['project'])
        datasets = cirro.datasets.list(input_params['project'])
        input_params = gather_download_arguments_dataset(input_params, datasets)
        files = cirro.datasets.get_file_listing(input_params['project'], input_params['dataset'])
        files_to_download = ask_dataset_files(files)

    project_id = get_id_from_name(projects, input_params['project'])
    dataset_id = input_params['dataset']

    cirro.datasets.download_files(project_id=project_id,
                                  dataset_id=dataset_id,
                                  download_location=input_params['data_directory'],
                                  files=files_to_download)


def run_configure_workflow():
    """Configure a workflow to be run in the Data Portal as a process."""
    _check_configure()
    cirro = Cirro()
    process_options = cirro.processes.list(process_type=Executor.NEXTFLOW)
    resources_folder, repo_prefix = get_output_resources_path()

    workflow = WorkflowConfigBuilder(repo_prefix)

    # Process record
    repo = get_repository()
    workflow.with_repository(repo)

    # Prompt for optional pre-process script
    if (preprocess_py := get_preprocess_script()) is not None:
        workflow.with_preprocess(preprocess_py)

    workflow.with_child_processes(
        get_child_processes(process_options)
    )

    # Process compute
    workflow.with_compute()

    # Process form & process inputs
    nf_schema = get_nextflow_schema(repo.repo_path, repo.version)
    inputs = {}
    if nf_schema is not None:
        form = {**nf_schema}
        convert_nf_schema(form, inputs)

        workflow.with_description(nf_schema['description'])
        workflow.with_form_inputs(form)

    else:
        workflow.with_description(get_description())
        form, inputs = prompt_user_inputs()
        workflow.with_form_inputs(form)

    # Inputs based on form config
    workflow.with_inputs(inputs)

    # Additional process inputs
    for input_name, input_value in get_additional_inputs():
        workflow.with_input(input_name, input_value)

    # Process outputs
    for output in get_outputs():
        workflow.with_output(output)
    workflow.with_common_outputs()

    # Save to resources
    workflow.save_local(resources_folder)


def run_configure():
    auth_method, auth_method_config, enable_additional_checksum = gather_auth_config()
    save_user_config(UserConfig(auth_method=auth_method,
                                auth_method_config=auth_method_config,
                                base_url=None,
                                transfer_max_retries=None,
                                enable_additional_checksum=enable_additional_checksum))


def _check_configure():
    """
    Prompts the user to do initial configuration if needed
    """
    if load_user_config() is not None:
        return

    run_configure()
