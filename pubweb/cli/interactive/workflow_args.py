from pathlib import Path
from typing import Union

import github
from github import Github
from github.Branch import Branch
from github.GitRelease import GitRelease
from github.Repository import Repository

from pubweb.cli.interactive.utils import ask, ask_yes_no
from pubweb.api.models.workflow_models import OptimizedOutput, Column, WorkflowRepository


def get_output_resources_path():
    """Get the location of the folder within the pubweb resources repository to write to."""

    # Get the base directory of the repository
    repo_folder = _get_repo_folder()

    # Build the subdirectory for the process
    subdirectory = ask(
        "text",
        "What subdirectory within the process/ folder which should be used to save the outputs?"
        " (e.g. hutch/fastqc/1.0)",
        required=True
    )

    resources_folder = Path(repo_folder, "process", subdirectory)

    # Check that the resources folder already exists and prompt until confirmed
    while resources_folder.exists():

        if ask(
                "select",
                "That folder already exists, would you like to overwrite any existing files or select a new folder?",
                choices=[f"Use {resources_folder}", "Select another"]
        ) == "Select another":

            # Build the subdirectory for the process
            subdirectory = ask(
                "text",
                "What subdirectory within the process/ folder which should be used to save the outputs?"
                " (e.g. hutch/fastqc/1.0)",
                required=True
            )
            resources_folder = Path(repo_folder, "process", subdirectory)

        else:
            break

    return resources_folder, subdirectory


def _get_repo_folder():
    """Get the base location of the pubweb resources repository."""

    repo_folder = ask(
        "path",
        "What folder contains a local copy of the PubWeb resources repository?",
        default=Path.cwd(),
        only_directories=True
    )
    repo_folder = Path(repo_folder)

    # If the path does not exist
    if not repo_folder.exists():

        # Ask if it should be created
        resp = ask(
            "select",
            f"The path does not exist: {repo_folder}\nWould you like to create it, or pick another folder?",
            choices=[
                "Create the folder",
                "Select another"
            ]
        )

        if resp == "Create the folder":
            repo_folder.mkdir(parents=True)
            return repo_folder

        else:
            return _get_repo_folder()

    else:
        return repo_folder


def get_child_processes(processes):
    # Get a list of the processes which are available
    process_choices = [
        f"{process['name']}\n     {process['desc']}\n     {process['id']}"
        for process in processes
    ]
    process_choices.sort()

    return [
        p.split("\n")[-1].strip(" ")
        for p in ask(
            "checkbox",
            "Select any processes which can be run on the outputs of this workflow",
            choices=process_choices
        )
    ]


def get_outputs():
    outputs = []

    if ask(
            "confirm",
            "Does this workflow produce output files which should be indexed for visualization?"
    ):
        outputs.append(_add_single_output())

        while ask("confirm", "Would you like to add another?"):
            outputs.append(_add_single_output())

    return outputs


def _add_single_output() -> OptimizedOutput:
    # Get the path of the output file(s) relative to the output directory
    source = ask(
        "text",
        "\n  ".join([
            "What is the location of the output files(s) within the workflow output directory?",
            "Multiple files with the same format can be included using wildcard (*) characters.\n"
        ])
    )
    # TODO: automatically get details based on sample file

    # Get the value used to separate columns
    sep = ask(
        "text",
        "\n  ".join([
            "What is the character used to separate columns?",
            "e.g. ',' for CSV, '\\t' for TSV:"
        ])
    )

    name = ask("text", "Short name for output file(s)")
    desc = ask("text", "Longer description for output file(s)")
    url = ask("text", "Optional website documenting file contents")

    # Build the list of columns
    columns = []

    print("")

    while len(columns) == 0 or ask("confirm", "Are there additional columns to add?"):
        columns.append(Column(
            header=ask("text", "Column header (value in the first line of the file)"),
            display_name=ask("text", "Column name (to be displayed to the user)"),
            description=ask("text", "Column description (to be displayed to the user)")
        ))

    if ask(
            "confirm",
            "\n     ".join([
                               "File configuration:",
                               f"Path: {source}",
                               f"Sep: {sep}",
                               f"Name: {name}",
                               f"Description: {desc}",
                               f"Reference URL: {url}",
                               "Columns:"
                           ] + [
                               f"    {col.header} - {col.display_name} - {col.description}"
                               for col in columns
                           ] + [
                               "Is all of the information above correct?"
                           ])
    ):
        return OptimizedOutput(
            source_pattern=source,
            seperator=sep,
            name=name,
            description=desc,
            documentation_url=url,
            columns=columns
        )


def get_preprocess_script():
    """Ask if the user wants to add a preprocessing script."""

    if ask_yes_no("Would you like to use a preprocessing script?"):

        script_path = ask(
            "path",
            "What script should be used?",
            default=Path.cwd()
        )
        script_path = Path(script_path)

        while not script_path.exists():

            script_path = ask(
                "path",
                f"Path cannot be found ({script_path}) - please select another",
                default=script_path
            )

        return script_path


def get_repository() -> WorkflowRepository:
    github_connection = Github()

    name = ask(
        "text",
        "What name should be displayed for this workflow?",
        required=True
    )

    # Get the organization
    org = ask(
        'text',
        'Which GitHub organization is the workflow located within?',
        default='nf-core',
        required=True
    )

    # Get the repository
    repo_name = _prompt_repository(org, github_connection)

    # Get the repository object
    repo = github_connection.get_repo(f"{org}/{repo_name}")

    # Get the version
    version = _prompt_repository_version(repo)
    if isinstance(version, GitRelease):
        documentation_url = version.url
        tarball_url = version.tarball_url
        version_name = version.tag_name
    else:
        documentation_url = f"https://github.com/{org}/{repo_name}/tree/{version.name}"
        tarball_url = ''
        version_name = version.name

    entrypoint = ask(
        "text",
        "What is the primary entrypoint for the workflow in the repository?",
        default="main.nf"
    )
    try:
        repo.get_contents(entrypoint, version_name)
    except github.UnknownObjectException:
        print(f"Warning: {entrypoint} not found in {repo_name}")

    return WorkflowRepository(display_name=name,
                              org=org,
                              repo_name=repo_name,
                              version=version_name,
                              entrypoint=entrypoint,
                              private=repo.private,
                              documentation_url=documentation_url,
                              tarball=tarball_url)


def _prompt_repository(org, github_connection):
    """Prompt the user for a repository contained within an organization."""

    # Get a list of repos in that organization
    user = github_connection.get_user(org)
    repo_count = user.public_repos

    if repo_count < 500:
        repo_list = [
            repo.name for repo in github_connection.get_user(org).get_repos()
            if repo.name != '.github'
        ]

        # then use that to ask the user which repo to look at
        return ask(
            'autocomplete',
            'Which repository contains the workflow of interest? (use TAB to display options)',
            choices=repo_list
        )

    while True:
        repo_name = ask(
            'text',
            'Enter the name of the repository',
            required=True
        )

        try:
            user.get_repo(repo_name)
            return repo_name
        except github.UnknownObjectException:
            print('Repository name not valid')


def _prompt_repository_version(repo: Repository) -> Union[GitRelease, Branch]:
    """Parse the repository and ask the user which tag/version to use."""

    # The version will be specified with either a branch or a release
    version_type = ask(
        'select',
        'Should the workflow version be specified by branch or release tag',
        choices=['branch', 'release']
    )

    # If the user decided to select the version type by release (tag)
    if version_type == 'release':

        # Get the releases which are available
        version_list = repo.get_releases()
        pretty_version_list = [f"{x.tag_name} ({x.title})" for x in version_list]

        version = ask(
            'select',
            f'Which version of {repo.name} do you want to use?',
            choices=pretty_version_list
        )

        version = [x for x in version_list if f"{x.tag_name} ({x.title})" == version][0]
        return version

    else:

        assert version_type == "branch"

        # Select from the branches which are available
        branch = ask(
            'select',
            f'Which branch of {repo.name} do you want to use?',
            choices=[branch.name for branch in repo.get_branches()]
        )

        branch = repo.get_branch(branch)

        return branch


def get_description():
    return ask(
        "text",
        "What is the description of this workflow?"
    )


def get_additional_inputs():
    """Configure any additional inputs."""

    inputs = []
    if ask(
        "confirm",
        "Would you like to add any fixed parameter values?\n  These values will not change based on user input."
    ):
        if (input_param := _add_fixed_param_input()) is not None:
            inputs.append(input_param)

        while ask("confirm", "Would you like to add another?"):
            if (input_param := _add_fixed_param_input()) is not None:
                inputs.append(input_param)

    return inputs


def _add_fixed_param_input():
    """Allow the user to add a single key-value entry to the params."""

    # Allow the user to select some pubweb-specific elements
    param_type = ask(
        "select",
        "What type of parameter is this?",
        choices=[
            "Fixed value",
            "Location of data inputs",
            "Location of data outputs",
        ]
    )

    if param_type == "Fixed value":

        # Get a key-value pair
        param_key = ask("text", "Parameter key:")
        param_value = ask("text", "Parameter value:")

    elif param_type == "Location of data inputs":

        param_key = ask("text", "Parameter key:")
        param_value = "$.params.inputs[0].s3|/data/"

    elif param_type == "Location of data outputs":

        param_key = ask("text", "Parameter key:")
        param_value = "$.params.dataset.s3|/data/"

    else:
        raise AssertionError(f"Internal error: parameter type {param_type} is not configured")

    # Let the user confirm their entry
    if ask("confirm", f"Confirm: {param_key} = {param_value}"):
        return param_key, param_value
