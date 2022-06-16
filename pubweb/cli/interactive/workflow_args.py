from pathlib import Path

from pubweb.cli.interactive.utils import ask, ask_yes_no


def get_output_resources_path():
    """Get the location of the folder within the pubweb resources repository to write to."""

    # Get the base directory of the repository
    repo_folder = _get_repo_folder()

    # Build the subdirectory for the process
    subdirectory = ask(
        "text",
        "What subdirectory within the process/ folder which should be used to save the outputs?"
        " (e.g. hutch/fastqc/1.0)"
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
                " (e.g. hutch/fastqc/1.0)"
            )
            resources_folder = Path(repo_folder, "process", subdirectory)

        else:
            break

    return repo_folder, resources_folder


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
    if ask(
            "confirm",
            "Does this workflow produce output files which should be indexed for visualization?"
    ):

        _add_single_output()

        while ask("confirm", "Would you like to add another?"):
            _add_single_output()


def _add_single_output():
    # Get the path of the output file(s) relative to the output directory
    source = ask(
        "text",
        "\n  ".join([
            "What is the location of the output files(s) within the workflow output directory?",
            "Multiple files with the same format can be included using wildcard (*) characters.\n"
        ])
    )

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
        columns.append(dict(
            col=ask("text", "Column header (value in the first line of the file)"),
            name=ask("text", "Column name (to be displayed to the user)"),
            desc=ask("text", "Column description (to be displayed to the user)")
        ))


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


def get_repo():
    name = ask(
        "text",
        "What name should be displayed for this workflow?"
    )

    # Get the organization
    org = ask(
        'text',
        'Which GitHub organization is the workflow located within?',
        default='nf-core'
    )

    # Get the repository
    repo = _prompt_repository(org)

    # Get the version
    version = _prompt_repository_version(org, repo)

    entrypoint = ask(
        "text",
        "What is the primary entrypoint for the workflow in the repository?",
        default="main.nf"
    )

    privacy = ask(
        "select",
        "Is the GitHub repository public or private?",
        choices=["Public", "Private"],
        default="Public"
    )


def _prompt_repository(self, org):
    """Prompt the user for a repository contained within an organization."""

    # Get a list of repos in that organization
    repo_list = [
        repo.name for repo in self.gh.get_user(org).get_repos()
        if repo.name != '.github'
    ]

    # then use that to ask the user which repo to look at
    return prompt_wrapper({
        'type': 'list',
        'name': 'repo',
        'message': 'Which repository contains the workflow of interest?',
        'choices': repo_list,
        'default': None
    })['repo']


def _prompt_repository_version(self, org, repo_name):
    """Parse the repository and ask the user which tag/version to use."""

    # Get the repository object
    repo = self.gh.get_repo(f"{org}/{repo_name}")

    # The version will be specified with either a branch or a release
    version_type = prompt_wrapper({
        'type': 'list',
        'name': 'version_type',
        'message': 'Should the workflow version be specified by branch or release tag?',
        'choices': ['branch', 'release'],
        'default': None
    })['version_type']

    # If the user decided to select the version type by release (tag)
    if version_type == 'release':

        # Get the releases which are available
        version_list = [x for x in repo.get_releases()]
        pretty_version_list = [f"{x.tag_name} ({x.title})" for x in version_list]

        version_prompt = {
            'type': 'list',
            'name': 'version',
            'message': f"Which version of {repo_name} do you want to use?",
            'choices': pretty_version_list,
            'default': None
        }
        answers = prompt_wrapper(version_prompt)

        version = [x for x in version_list if f"{x.tag_name} ({x.title})" == answers['version']][0]

        # Set the URL of the tag
        self.process_config["dynamo"][
            "documentationUrl"] = f"https://github.com/{org}/{repo_name}/releases/tag/{version.tag_name}"

        # Set the URL of the tarball
        self.tarball_url = f"https://github.com/{org}/{repo_name}/archive/refs/tags/{version.tag_name}.tar.gz"

        return version.tag_name

    else:

        assert version_type == "branch"

        # Select from the branches which are available
        branch = prompt_wrapper({
            'type': 'list',
            'name': 'branch',
            'message': f"Which branch of {org}/{repo_name} do you want to use?",
            'choices': [branch.name for branch in repo.get_branches()],
            'default': None
        })['branch']

        # Set the URL of the branch
        self.process_config["dynamo"]["documentationUrl"] = f"https://github.com/{org}/{repo_name}/tree/{branch}"

        # Set the URL of the tarball
        self.tarball_url = f"https://github.com/{org}/{repo_name}/archive/refs/heads/{branch}.tar.gz"

        return branch
