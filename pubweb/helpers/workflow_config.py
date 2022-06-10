import json
import shutil
import tarfile

import requests
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

        # Save each of the items in the process configuration
        for k, v in self.process_config.items():

            # Use the dictionary key to drive the file name
            output_fp = os.path.join(self.output_folder, f"process-{k}.json")
            print(f"Writing out to {output_fp}")

            # Open the file
            with open(output_fp, "w") as handle:

                # Serialize as JSON
                json.dump(v, handle, indent=4)

        # Write the compute configuration
        output_fp = os.path.join(self.output_folder, "process-compute.config")

        with open(output_fp, "w") as handle:
            handle.write(self.compute_config)

        print(f"Boilerplate compute configuration has been written to {output_fp} -- please modify that file as necessary.")

        print(f"Done writing all process configuration items to {output_fp}")

    def _get_resources_repo(self):
        """Get the location of the folder within the pubweb resources repository to write to."""

        # Get the base directory of the repository
        repo_folder = self._get_repo_folder()

        # Build the subdirectory for the process
        subdirectory = ask(
            "text",
            "What subdirectory within the process/ folder which should be used to save the outputs? (e.g. hutch/fastqc/1.0)"
        )

        resources_folder = os.path.join(repo_folder, "process", subdirectory)

        # If the folder already exists
        while os.path.exists(resources_folder):

            if ask(
                "select",
                "That folder already exists, would you like to overwrite any existing files or select a new folder?",
                choices=[f"Use {resources_folder}", "Select another"]
            ) == "Select another":

                # Build the subdirectory for the process
                subdirectory = ask(
                    "text",
                    "What subdirectory within the process/ folder which should be used to save the outputs? (e.g. hutch/fastqc/1.0)"
                )
                resources_folder = os.path.join(repo_folder, "process", subdirectory)

            else:
                break

        # Create the folder if it does not exist
        if not os.path.exists(resources_folder):
            os.makedirs(resources_folder)

        # Return the full path to the folder, as well as the relative path within the repository
        return resources_folder, subdirectory.strip("/")

    def _get_preprocess_script(self):
        """Ask if the user wants to add a preprocessing script."""

        if ask(
            "select",
            "Would you like to use a preprocessing script?",
            choices=["Yes", "No"]
        ) == "Yes":

            script_path = ask(
                "path",
                "What script should be used?",
                default="./"
            )

            while not os.path.exists(script_path):

                script_path = ask(
                    "path",
                    f"Path cannot be found ({script_path}) - please select another",
                    default=script_path
                )

            return script_path

    def _get_repo_folder(self):
        """Get the base location of the pubweb resources repository."""

        repo_folder = ask(
            "path",
            "What folder contains a local copy of the PubWeb resources repository?",
            default="./",
            only_directories=True
        )

        # If the path does not exist
        if not os.path.exists(repo_folder):

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
                os.makedirs(repo_folder)
                return repo_folder

            else:
                return self._get_repo_folder()

        else:
            return repo_folder

    def _configure_repository(self):
        """Configure the workflow repository."""

        # Set up the boilerplate elements of the dynamo record
        self._add_dynamo_boilerplate()

        # Get the name of the process
        self.process_config["dynamo"]["name"] = ask(
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

        # Get the folder which should be used to write the outputs,
        # as well as the path relative to the repository
        self.output_folder, self.repo_prefix = self._get_resources_repo()

        # Ask if the user wants to add a preprocessing script
        preprocess_py = self._get_preprocess_script()

        # If they did want to include one
        if preprocess_py is not None:

            # Copy it to the output folder
            shutil.copyfile(
                preprocess_py, 
                os.path.join(self.output_folder, preprocess_py.split("/")[-1])
            )

            # Add it to the dynamo record
            self.process_config["dynamo"]["preProcessScript"] = f"s3://<RESOURCES_BUCKET>/{self.repo_prefix}/{preprocess_py.split('/')[-1]}"

        # Use the relative path within the repository to set up the relative
        # paths in the dynamo record
        self.process_config["dynamo"]["computeDefaults"] = [
            {
                "executor": "NEXTFLOW",
                "json": f"s3://<RESOURCES_BUCKET>/{self.repo_prefix}/process-compute.config",
                "name": "Default"
            }
        ]

        self.process_config["dynamo"]["paramMapJson"] = f"s3://<RESOURCES_BUCKET>/{self.repo_prefix}/process-input.config"
        self.process_config["dynamo"]["formJson"] = f"s3://<RESOURCES_BUCKET>/{self.repo_prefix}/process-form.config"
        self.process_config["dynamo"]["webOptimizationJson"] = f"s3://<RESOURCES_BUCKET>/{self.repo_prefix}/process-output.config"

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
            self.process_config["dynamo"]["documentationUrl"] = f"https://github.com/{org}/{repo_name}/releases/tag/{version.tag_name}"

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

    def _configure_compute(self):
        """Configure the compute configuration."""
        
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

    def _configure_form(self):
        """Configure the form."""

        # Download the repository tarball and return the local filename
        repo_tarball = self._get_repo_tarball()

        # Try to parse a nextflow_schema.json file, if present
        self.nf_schema = self.get_nextflow_schema(repo_tarball)

        # If a nextflow_schema.json is present
        if self.nf_schema is not None:

            # Set the description from the schema
            self.process_config["dynamo"]["desc"] = self.nf_schema["description"]

            # Make sure that the schema has the expected top-level entries
            for k in ["title", "definitions"]:
                assert k in self.nf_schema, f"Did not find '{k}' in the nextflow schema as expected"

            # Get all of the process-related parameters, based on the nextflow schema
            self.process_config["form"] = dict(
                ui=dict(),
                # In addition to modifying the schema contents, we will
                # also ask the user if they want to include or exclude each option
                form=self._convert_nf_schema(self.nf_schema)
            )
            
        # Otherwise
        else:

            # Get the description of the process
            self.process_config["dynamo"]["desc"] = ask(
                "text",
                "What is the description of this workflow?"
            )

            # Get all of the process-related parameters, based just on user input
            self.process_config["form"] = dict(
                ui=dict(),
                form=self._prompt_user_inputs()
            )

    def _get_repo_tarball(self):

        """Clone a local copy of the repository which will be imported/parsed."""
        file_name = os.path.basename(self.tarball_url)
        print(f"Downloading {file_name} from {self.tarball_url}")
        
        r = requests.get(self.tarball_url, allow_redirects=True)
        with open(file_name, 'w+b') as f:
            f.write(r.content)
        return file_name
        
    def get_nextflow_schema(self, repo_tarball):
        """If a nextflow_schema.json is present, parse it and prompt the user for any modifications."""

        with tarfile.open(repo_tarball, 'r') as archive:
            archive_list = archive.getmembers()
            nextflow_schema_list = [x for x in archive_list if x.name.find('nextflow_schema.json') >= 0]
            if len(nextflow_schema_list) > 0:
                nextflow_schema_file = nextflow_schema_list[0].name
                archive.extract(nextflow_schema_file, path='tmp')
                local_nf_schema_file = f"tmp/{nextflow_schema_file}"
                with open(local_nf_schema_file, 'r') as f:
                    nf_schema = json.loads(f.read())
                    return nf_schema
            else:
                print(f"No nextflow_schema.json file found, switching to DIY mode")
                return None

    def _convert_nf_schema(self, obj, param_root="$.params.dataset.paramJson"):
        """
        Given a nextflow schema object, parse it and 
        run the user through prompts to determine which fields to expose
        """

        # Remove any unwanted keys
        for k in ["$schema", "$id", "fa_icon", "mimetype", "allOf", "schema"]:
            if k in obj:
                del obj[k]

        # Convert the 'definitions' from the Nextflow schema to 'properties' of the form
        if "definitions" in obj:
            obj["properties"] = obj["definitions"]
            del obj["definitions"]

        # The object should have a "type"
        assert "type" in obj, f"Expected 'type':\n({json.dumps(obj, indent=4)})"

        # If this is an object
        if obj["type"] == "object":

            # It must have "properties"
            assert "properties" in obj, f"Expected 'properties' when type='object':\n({json.dumps(obj, indent=4)})"

            # Give the user the option to remove items from that list

            # First ask the user which options should be kept
            option_list = [
                f"{k}\n     {v.get('description')}"
                for k, v in obj["properties"].items()
            ]
            to_keep = ask(
                "checkbox",
                "Please select the items to display to the user\n<space> to select/deselect, <enter> when done",
                choices=option_list
            )

            # Remove the description from the list of 
            to_keep = [i.split("\n")[0] for i in to_keep]

            # Subset the defs to only keep the selected options
            obj["properties"] = {
                k: obj["properties"][k]
                for k in to_keep
            }

            # If there is a "required" field at the top level
            if "required" in obj:

                # Only keep the required items which were selected
                obj["required"] = [i for i in obj["required"] if i in to_keep]

            # Now convert each of those objects in a recursive way
            obj["properties"] = {
                k: self._convert_nf_schema(v, param_root=f"{param_root}.{k}")
                for k, v in obj["properties"].items()
            }

            # For each of those elements
            for k, v in obj["properties"].items():

                # Skip any other objects
                if v["type"] == "object":
                    continue

                # Any other type needs to be added to the inputs

                # Make sure that this parameter name doesn't collide with anything else
                assert k not in self.process_config["input"], f"Error, found two elements in the form named {k}"

                # Add it to the inputs
                self.process_config["input"][k] = f"{param_root}.{k}"

        # Return the object
        return obj

    def _configure_inputs(self):
        """Configure any additional inputs."""

        if ask(
            "confirm",
            "Would you like to add any fixed parameter values?\n     These values will not change based on user input."
        ):

            self._add_fixed_param_input()

            while ask("confirm", "Would you like to add another?"):

                self._add_fixed_param_input()

    def _add_fixed_param_input(self):
        """Allow the user to add a single key-value entry to the params."""

        # Get a key-value pair
        param_key = ask("text", "Parameter key:")
        param_value = ask("text", "Parameter value:")

        # Let the user confirm their entry
        if ask("confirm", f"Confirm: {param_key} = {param_value}"):
            self.process_config["input"][param_key] = param_value

    def _configure_outputs(self):
        """Configure any additional outputs."""

        # Set up the blank output object
        self.process_config["output"] = dict(commands=[])

        if ask(
            "confirm",
            "Does this workflow produce output files which should be indexed for visualization?"
        ):

            self._add_single_output()

            while ask("confirm", "Would you like to add another?"):

                self._add_single_output()

        # Add the commands to index all of the files which were output
        self.process_config["output"]["commands"].extend([
            {
                "command": "hot.Manifest",
                "params": {}
            },
            {
                "command": "save.ManifestJson",
                "params": {
                    "files": [
                    {
                        "glob": "$dataDirectory/**/*.*"
                    }
                    ],
                    "tables": [],
                    "jsons": [],
                    "lists": [],
                    "tensors": [],
                    "version": "2"
                }
            }
        ])

    def _add_single_output(self):
        """Configure a single output file."""

        # Get the path of the output file(s) relative to the output directory
        source = ask(
            "text", 
            "\n     ".join([
                "What is the location of the output files(s) within the workflow output directory?",
                "Multiple files with the same format can be included using wildcard (*) characters."
            ])
        )

        # Get the value used to separate columns
        sep = ask(
            "text", 
            "\n     ".join([
                "What is the character used to separate columns?",
                "e.g. ',' for CSV, '\t' for TSV"
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

        # Let the user confirm
        if ask(
            "confirm", 
            "\n     ".join([
                "File configuration:",
                f"Path: {source}",
                f"Sep: {sep}",
                f"Name: {name}",
                f"Description: {desc}",
                f"Reference URL: {url}",
                f"Columns:"
            ] + [
                f"    {col['col'] - col['name'] - col['desc']}"
                for col in columns
            ] + [
                "Is all of the information above correct?"
            ])
        ):

            self.process_config["output"]["commands"].append(
                dict(
                    command="Hot.Dsv",
                    params=dict(
                        url=url,
                        source=source,
                        sep=sep,
                        header=True,
                        name=name,
                        desc=desc,
                        cols=columns
                    )
                )
            )
