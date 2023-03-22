from cirro.api.clients.portal import DataPortalClient
from cirro.api.config import UserConfig, save_user_config
from cirro.api.models.dataset import CreateIngestDatasetInput
from cirro.api.models.process import Executor
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
from cirro.file_utils import get_files_in_directory
from cirro.helpers import WorkflowConfigBuilder


def run_list_datasets(input_params: ListArguments, interactive=False):
    """List the datasets available in a particular project."""

    # Instantiate the Cirro Data Portal client
    cirro = DataPortalClient()

    # If the user provided the --interactive flag
    if interactive:

        # Get the list of projects available to the user
        projects = cirro.project.list()

        if len(projects) == 0:
            print("No projects available")
            return

        # Prompt the user for the project
        input_params = gather_list_arguments(input_params, projects)

    # List the datasets available in that project
    datasets = cirro.dataset.find_by_project(input_params['project'])

    sorted_datasets = sorted(datasets, key=lambda d: d.created_at, reverse=True)
    print("\n\n".join([f'Name: {dataset.name}\n'
                       f'Desc: {dataset.description}\n'
                       f'GUID: ({dataset.id})'
                       for dataset in sorted_datasets]))


def run_ingest(input_params: UploadArguments, interactive=False):
    cirro = DataPortalClient()
    projects = cirro.project.list()
    processes = cirro.process.list(process_type=Executor.INGEST)

    if len(projects) == 0:
        print("No projects available")
        return

    if interactive:
        input_params = gather_upload_arguments(input_params, projects, processes)

    directory = input_params['data_directory']
    files = get_files_in_directory(directory)
    if len(files) == 0:
        raise RuntimeWarning("No files to upload, exiting")

    process = get_item_from_name_or_id(processes, input_params['process'])
    cirro.process.check_dataset_files(files, process.id, directory)

    create_request = CreateIngestDatasetInput(
        project_id=get_id_from_name(projects, input_params['project']),
        process_id=process.id,
        name=input_params['name'],
        description=input_params['description'],
        files=files
    )

    create_resp = cirro.dataset.create(create_request)

    cirro.dataset.upload_files(dataset_id=create_resp['datasetId'],
                               project_id=create_request.project_id,
                               directory=directory,
                               files=files)


def run_download(input_params: DownloadArguments, interactive=False):
    cirro = DataPortalClient()

    projects = cirro.project.list()

    if len(projects) == 0:
        print("No projects available")
        return

    files_to_download = None
    if interactive:
        input_params = gather_download_arguments(input_params, projects)

        input_params['project'] = get_id_from_name(projects, input_params['project'])
        datasets = cirro.dataset.find_by_project(input_params['project'])
        input_params = gather_download_arguments_dataset(input_params, datasets)
        dataset_files = cirro.dataset.get_dataset_files(input_params['project'], input_params['dataset'])
        files_to_download = ask_dataset_files(dataset_files)

    dataset_params = {
        'project': get_id_from_name(projects, input_params['project']),
        'dataset': input_params['dataset']
    }

    cirro.dataset.download_files(project_id=dataset_params['project'],
                                 dataset_id=dataset_params['dataset'],
                                 download_location=input_params['data_directory'],
                                 files=files_to_download)


def run_configure_workflow():
    """Configure a workflow to be run in the Data Portal as a process."""

    cirro = DataPortalClient()
    process_options = cirro.process.list(process_type=Executor.NEXTFLOW)
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
    auth_method, auth_method_config = gather_auth_config()
    save_user_config(UserConfig(auth_method=auth_method,
                                auth_method_config=auth_method_config,
                                base_url=None))
