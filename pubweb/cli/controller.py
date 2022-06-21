from pathlib import Path

from pubweb.cli.interactive import gather_list_arguments, gather_upload_arguments, gather_download_arguments, gather_download_arguments_dataset, gather_login
from pubweb.auth import UsernameAndPasswordAuth
from pubweb.cli.interactive.workflow_args import get_preprocess_script, get_inputs, get_outputs, get_child_processes, \
    get_repository, get_description
from pubweb.cli.models import ListArguments, UploadArguments, DownloadArguments
from pubweb.config import AuthConfig, save_config, load_config
from pubweb.file_utils import get_files_in_directory
from pubweb.helpers import WorkflowConfigBuilder
from pubweb.helpers.schema_helpers import get_nextflow_schema, convert_nf_schema
from pubweb.utils import parse_json_date, format_date
from pubweb import PubWeb


def get_credentials():
    config = load_config()
    return config.username, config.password


def run_list_datasets(input_params: ListArguments, interactive=False):
    """List the datasets available in a particular project."""

    # Instantiate the PubWeb client
    pubweb = PubWeb(UsernameAndPasswordAuth(*get_credentials()))

    # If the user provided the --interactive flag
    if interactive:

        # Get the list of projects available to the user
        projects = pubweb.project.list()

        # Prompt the user for the project
        input_params = gather_list_arguments(input_params, projects)

    # List the datasets available in that project
    datasets = pubweb.dataset.find_by_project(input_params['project'])

    sorted_datasets = sorted(datasets, key=lambda d: parse_json_date(d["createdAt"]), reverse=True)
    print("\n\n".join([f'Name: {dataset["name"]}\nDesc: {dataset["desc"]}\nGUID: ({dataset["id"]})' for dataset in sorted_datasets]))
    

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


def run_configure_workflow():
    """Configure a workflow to be run in the Data Portal as a process."""

    pubweb = PubWeb(UsernameAndPasswordAuth(*get_credentials()))
    process_options = pubweb.process.list(process_type='NEXTFLOW')

    repo_prefix = get_repo_prefix()
    workflow = WorkflowConfigBuilder(repo_prefix)

    # Process record
    repo = get_repository()
    workflow.with_repository(repo)

    preprocess_py = get_preprocess_script()
    if preprocess_py is not None:
        workflow.with_preprocess(preprocess_py)

    workflow.with_child_processes(
        get_child_processes(process_options)
    )

    # Process form & process inputs
    nf_schema = get_nextflow_schema(repo.repo_path, repo.version)
    if nf_schema is not None:
        inputs = {}
        form = {**nf_schema}
        convert_nf_schema(form, inputs)

        workflow.with_description(nf_schema['description'])
        workflow.with_form_inputs()

        for input_name, input_value in inputs.items():
            workflow.with_input(input_name, input_value)

    else:
        workflow.with_description(get_description())
        workflow.with_form_inputs()

    # Additional inputs
    for input_name, input_value in get_inputs():
        workflow.with_input(input_name, input_value)

    # Process outputs
    for output in get_outputs():
        workflow.with_output(output)
    workflow.with_common_outputs()

    workflow.save_local(Path.cwd())


def run_configure():
    username, password = gather_login()
    auth_config = AuthConfig(username, password)
    save_config(auth_config)
