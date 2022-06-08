from github import Github
from questionary import prompt


def prompt_wrapper(questions):
    answers = prompt(questions)
    # Prompt catches KeyboardInterrupt and sends back an empty dictionary
    # We want to catch this exception
    if len(answers) == 0:
        raise KeyboardInterrupt()
    return answers


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

        pass

    def _configure_repository(self):
        """Configure the workflow repository."""

        # Get the organization
        org = prompt_wrapper({
            'type': 'input',
            'name': 'org',
            'message': 'Which GitHub organization is the workflow located within?',
            'default': 'nf-core'
        })["org"]

        # Get the repository
        repo = self._prompt_repository(org)

        # Get the version
        version = self._prompt_repository_version(org, repo)

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

    def _prompt_repository(self, org):
        """Prompt the user for a repository contained within an organization."""

        # Get a list of repos in that organization
        repo_list = [repo.name for repo in self.gh.get_user(org).get_repos()]

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

