import json
from github import Github
import os
import questionary


def prompt_wrapper(questions):
    answers = questionary.prompt(questions)
    # Prompt catches KeyboardInterrupt and sends back an empty dictionary
    # We want to catch this exception
    if len(answers) == 0:
        raise KeyboardInterrupt()
    return answers


def type_validator(t, v):
    """Return a boolean indicating whether `v` can be cast to `t(v)` without raising a ValueError."""
    try:
        t(v)
        return True
    except ValueError:
        return False


def ask(fname, msg, validate_type=None, output_f=None, **kwargs) -> str:
    """Wrap questionary functions to catch escapes and exit gracefully."""

    # Get the questionary function
    questionary_f = questionary.__dict__.get(fname)

    # Make sure that the function exists
    assert questionary_f is not None, f"No such questionary function: {fname}"

    if fname == "select":
        kwargs["use_shortcuts"] = True

    if validate_type is not None:
        kwargs["validate"] = lambda v: type_validator(validate_type, v)

    # The default value must be a string
    if kwargs.get("default") is not None:
        kwargs["default"] = str(kwargs["default"])

    # Add a spacer line before asking the question
    print("")

    # Get the response
    resp = questionary_f(msg, **kwargs).ask()

    # If the user escaped the question
    if resp is None:
        raise KeyboardInterrupt()

    # If an output transformation function was defined
    if output_f is not None:

        # Call the function
        resp = output_f(resp)

    # Otherwise
    return resp


class WorkflowConfig:

    def __init__(self, client):
        """Initialize the workflow configuration object with a PubWeb client."""
        
        # Attach the client
        self.client = client

        # Connect to GitHub
        self.gh = Github()

        # All of the parameters will be added to a single object
        self.process_config = dict(
            dynamo=dict(),
            form=dict(),
            input=dict(),
            output=dict()
        )

        # The compute configuration is boilerplate at this point
        self.compute_config = """profiles {
    standard {
        process {
            executor = 'awsbatch'
            errorStrategy = 'retry'
            maxRetries = 2
        }
    }
}
"""

    def configure(self):
        """Main method for getting user input, parsing the repo, and creating process docs."""

        # Configure the workflow repository
        # used to populate process-dynamo.json
        self._configure_repository()

        # Configure the compute configuration
        # used to populate process-compute.config
        self._configure_compute()

        # Configure the form
        self._configure_form()
        # used to populate process-form.json and process-input.json

        # Configure any additional inputs
        # used to add to process-input.json
        self._configure_inputs()

        # Configure outputs
        # used to configure process-output.json
        self._configure_outputs()

    def save_local(self):
        """Write out the workflow configuration as a collection of files."""

        # Get the folder to use for outputs
        output_folder = self._get_output_folder()

        # Save each of the items in the process configuration
        for k, v in self.process_config.items():

            # Use the dictionary key to drive the file name
            output_fp = f"process-{k}.json"
            print(f"Writing out to {output_fp}")

            # Open the file
            with open(output_fp, "w") as handle:

                # Serialize as JSON
                json.dump(v, handle, indent=4)

        # Write the compute configuration
        output_fp = os.path.join(output_folder, "process-compute.config")

        with open(output_fp, "w") as handle:
            handle.write(self.compute_config)

        print(f"Boilerplate compute configuration has been written to {output_fp} -- please modify that file as necessary.")

        print(f"Done writing all process configuration items to {output_fp}")

    def _get_output_folder(self):
        """Get the output folder """

        output_folder = ask(
            "path",
            "What folder should be used to write the workflow configuration?",
            default="./",
            only_directories=True
        )

        # If the path does not exist
        if not os.path.exists(output_folder):

            # Ask if it should be created
            resp = ask(
                "select",
                f"The path does not exist: {output_folder}\nWould you like to create it, or pick another folder?",
                choices=[
                    "Create the folder",
                    "Select another"
                ]
            )

            if resp == "Create the folder":
                os.makedirs(output_folder)
                return output_folder

            else:
                return self._get_output_folder()

        else:
            return output_folder

    def _configure_repository(self):
        """Configure the workflow repository."""

        # Set up the boilerplate elements of the dynamo record
        self._add_dynamo_boilerplate()

        # Get the organization
        org = ask(
            'text',
            'Which GitHub organization is the workflow located within?',
            default='nf-core'
        )

        # Get the repository
        repo = self._prompt_repository(org)

        # Get the version
        version = self._prompt_repository_version(org, repo)

        # Set up the process name based on the workflow/version
        process_id = f"process-{org}-{repo}-{version}"
        self.process_config["dynamo"]["id"] = process_id

        # Get the entrypoint to use
        entrypoint = prompt_wrapper(dict(
            type="input",
            name="entrypoint",
            message="What is the primary entrypoint for the workflow in the repository?",
            default="main.nf"
        ))["entrypoint"]

        # Check if the repository is public or private
        privacy = prompt_wrapper(dict(
            type="list",
            message="Is the GitHub repository public or private?",
            choices=["Private", "Public"],
            default="Public",
            name="privacy"
        ))["privacy"]

        # Set up the 'code' block of the dynamo record
        self.process_config["dynamo"]["code"] = dict(
            repository=f"GITHUB{privacy.upper()}",
            script=entrypoint,
            uri=f"{org}/{repo}",
            version=version
        )

        # Add any child processes that may exist
        self.process_config["dynamo"]["childProcessIds"] = [
            p.split("\n")[-1].strip(" ")
            for p in ask(
                "checkbox",
                "Select any processes which can be run on the outputs of this workflow",
                choices=[
                    f"{process['name']}\n     {process['desc']}\n     {process['id']}"
                    for process in self.client.process.list(process_type='NEXTFLOW')
                ]
            )
        ]

    def _add_dynamo_boilerplate(self):
        """Add the elements of the dynamo record which do not vary by user entry."""

        self.process_config["dynamo"]["executor"] = "NEXTFLOW"
        self.process_config["dynamo"]["paramDefaults"] = []
        self.process_config["dynamo"]["fileJson"] = ""
        self.process_config["dynamo"]["componentJson"] = ""
        self.process_config["dynamo"]["infoJson"] = ""

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

        # If the user decided to select the version type by branch
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
            return version.tag_name

        else:

            assert version_type == "branch"

            # Select from the branches which are available
            return prompt_wrapper({
                'type': 'list',
                'name': 'branch',
                'message': f"Which branch of {org}/{repo_name} do you want to use?",
                'choices': [branch.name for branch in repo.get_branches()],
                'default': None
            })['branch']

    def _configure_compute(self):
        """Configure the compute configuration."""

        pass

    def _configure_form(self):
        """Configure the form."""

        pass

    def _configure_inputs(self):
        """Configure any additional inputs."""

        pass

    def _configure_outputs(self):
        """Configure any additional outputs."""

        pass

