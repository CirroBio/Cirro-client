import json
import os
import shutil
import tarfile
from pathlib import Path

import requests
from github import Github

from pubweb.cli.interactive.utils import prompt_wrapper, ask, ask_yes_no
from pubweb.helpers.constants import IGENOMES_REFERENCES, S3_RESOURCES_PREFIX


class WorkflowConfig:
    def __init__(self, client):
        """Initialize the workflow configuration object with a PubWeb client."""
        
        # Attach the client
        self.client = client

        # Connect to GitHub
        self.gh = Github()

        # All the parameters will be added to a single object
        self.process_config = dict(
            dynamo=dict(),
            form=dict(),
            input=dict(),
            output=dict()
        )

        self.compute_config = ""
        self.output_folder = Path.cwd()

    def save_local(self):
        """Write out the workflow configuration as a collection of files."""

        # Save each of the items in the process configuration
        for config_name, config_value in self.process_config.items():
            output_fp = Path(self.output_folder, f"process-{config_name}.json")
            print(f"Writing out to {output_fp}")

            with output_fp.open('w') as handle:
                json.dump(config_value, handle, indent=4)

        # Write the compute configuration
        compute_path = Path(self.output_folder, "process-compute.config")

        with compute_path.open("w") as handle:
            handle.write(self.compute_config)

        print(f"Boilerplate compute configuration has been written to {self.output_folder}"
              f" -- please modify that file as necessary.")

        print(f"Done writing all process configuration items to {self.output_folder}")

    def with_repository(self,
                        name: str,
                        org: str,
                        repo: str,
                        version: str,
                        entrypoint='main.nf',
                        private=False) -> self:
        """Configure the workflow repository."""

        # Set up the boilerplate elements of the dynamo record
        self._add_dynamo_boilerplate()

        # Get the name of the process
        self.process_config["dynamo"]["name"] = name

        # Set up the process name based on the workflow/version
        process_id = f"process-{org}-{repo}-{version}"
        self.process_config["dynamo"]["id"] = process_id

        repository_code = f"GITHUB{'PRIVATE' if private else 'PUBLIC'}"
        # Set up the 'code' block of the dynamo record
        self.process_config["dynamo"]["code"] = dict(
            repository=repository_code,
            script=entrypoint,
            uri=f"{org}/{repo}",
            version=version
        )

        # Get a list of the processes which are available
        process_choices = [
            f"{process['name']}\n     {process['desc']}\n     {process['id']}"
            for process in self.client.process.list(process_type='NEXTFLOW')
        ]
        process_choices.sort()

        # Add any child processes that may exist
        self.process_config["dynamo"]["childProcessIds"] = [
            p.split("\n")[-1].strip(" ")
            for p in ask(
                "checkbox",
                "Select any processes which can be run on the outputs of this workflow",
                choices=process_choices
            )
        ]

        # Use the relative path within the repository to set up the relative
        # paths in the dynamo record
        self.process_config["dynamo"]["paramMapJson"] = \
            f"{S3_RESOURCES_PREFIX}/{self.repo_prefix}/process-input.json"
        self.process_config["dynamo"]["formJson"] = \
            f"{S3_RESOURCES_PREFIX}/{self.repo_prefix}/process-form.json"
        self.process_config["dynamo"]["webOptimizationJson"] = \
            f"{S3_RESOURCES_PREFIX}/{self.repo_prefix}/process-output.json"

        return self

    def with_preprocess(self, preprocess_py_path: Path):
        shutil.copyfile(
            preprocess_py_path,
            Path(self.output_folder, preprocess_py_path.name)
        )

        # Add it to the dynamo record
        self.process_config["dynamo"]["preProcessScript"] = \
            f"{S3_RESOURCES_PREFIX}/{self.repo_prefix}/{preprocess_py_path.name}"

        return self

    def _add_dynamo_boilerplate(self):
        """Add the elements of the dynamo record which do not vary by user entry."""

        self.process_config["dynamo"]["executor"] = "NEXTFLOW"
        self.process_config["dynamo"]["paramDefaults"] = []
        self.process_config["dynamo"]["fileJson"] = ""
        self.process_config["dynamo"]["componentJson"] = ""
        self.process_config["dynamo"]["infoJson"] = ""

    def with_compute(self, max_retry=2):
        """
        Configure the compute configuration.
        The compute configuration is boilerplate at this point
        """

        self.process_config["dynamo"]["computeDefaults"] = [
            {
                "executor": "NEXTFLOW",
                "json": f"{S3_RESOURCES_PREFIX}/{self.repo_prefix}/process-compute.config",
                "name": "Default"
            }
        ]

        self.compute_config = f"""profiles {{
    standard {{
        process {{
            executor = 'awsbatch'
            errorStrategy = 'retry'
            maxRetries = {max_retry}
        }}
    }}
}}
"""
        return self

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
                print(f"No nextflow_schema.json file found, please specify any required inputs")
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

    def _prompt_user_inputs(self):
        """Prompt for user inputs which should be included in the form."""

        # Make a dict with the properties which should be rendered in the form
        # Each parameter will fall inside a section with its own title
        properties = dict()

        print("The form which is presented to the user is broken into sections, each with its own heading")

        while len(properties) == 0 or ask("confirm", "Would you like to add another section of parameters?"):

            # Get the contents of this section
            section_key, section_contents = self._prompt_user_input_section()

            # Add those contents to the form
            properties[section_key] = section_contents

        return properties

    def _prompt_user_input_section(self):
        """Ask the user for all of the parameters which are found in a single section of the input form."""

        section_title = ask("text", "What is the title of this section?")

        # Format the section key based on the title
        section_key = section_title.lower().replace(" ", "_").replace("-", "_")

        # Build a dict of the individual form entries
        properties = dict()

        # Keep track of which inputs are required
        required = []

        for input_key, input_val, input_required in self._yield_form_input_single(section_key):

            properties[input_key] = input_val
            if input_required:
                required.append(input_key)

        # Return the fully formulated section
        section_contents = dict(
            type="object",
            title=section_title,
            required=required,
            properties=properties
        )
        return section_key, section_contents

    def _yield_form_input_single(self, section_key):
        """Allow the user to add as many form inputs as they require."""

        initial = True

        while initial or ask("confirm", "Would you like to add another parameter to this section?"):
            initial = False

            yield self._prompt_form_input_single(section_key)

    def _prompt_form_input_single(self, section_key):
        """Prompt the user for a single element in the form."""

        # Prompt for the parameter key
        kw = ask("text", "Parameter key used in workflow")

        # There should be no collision between keys
        while len(kw) == 0 or kw in self.process_config["input"]:
            kw = ask("text", f"Parameter key is not valid or has already been used, please select another")

        elem = dict()
        elem["title"] = ask("text", "Parameter title")
        elem["description"] = ask("text", "Parameter description")
        required = ask_yes_no("Is this parameter required?")

        # Get the type of input
        prompt_type = ask(
            "select",
            "What type of input should the user provide?",
            choices=[
                "Text entry",
                "Choose from list",
                "Boolean",
                "Number",
                "File from the input dataset",
                "File from a project reference",
                "List of iGenomes references",
            ]
        )

        if prompt_type == "Text entry":
            elem["type"] = "string"
            if ask_yes_no("Does this input have a default value?"):
                elem["default"] = ask("text", "Default value: ")

        elif prompt_type == "Choose from list":
            print("Please set up the options which the user can choose between")
            print("Note that you can customize the value displayed to the user")
            elem["type"] = "string"
            elem["enum"] = []
            elem["enumNames"] = []

            while len(elem["enum"]) == 0 or ask_yes_no("Would you like to add another option?"):

                val = ask("text", "Value:")
                name = ask("text", "Display:", default=val)

                elem["enum"].append(val)
                elem["enumNames"].append(name)

        elif prompt_type == "Boolean":
            elem["type"] = "boolean"
            if ask_yes_no("Does this input have a default value?"):
                elem["default"] = ask("select", "Default value:", choices=["True", "False"]) == "True"

        elif prompt_type == "Number":
            if ask_yes_no("Does this input have a default value?"):
                if ask("select", "Integer or float?", choices=["Integer", "Float"]) == "Integer":
                    elem["default"] = int(ask("text", "Default value:", validate_type=int))
                    elem["type"] = "integer"
                else:
                    elem["default"] = float(ask("text", "Default value:", validate_type=float))
                    elem["type"] = "number"

        elif prompt_type == "List of iGenomes references":
            elem["type"] = "string"
            elem["enum"] = IGENOMES_REFERENCES.keys()
            elem["enumNames"] = IGENOMES_REFERENCES.values()

        elif prompt_type == "File from the input dataset":

            elem["type"] = "string"
            elem["file"] = f"**/*{ask('text', 'What is the expected file extension?')}"
            elem["pathType"] = "dataset"
            elem["mm"] = dict(matchBase=True)

        elif prompt_type == "File from a project reference":

            elem["type"] = "string"
            elem["pathType"] = "references"

            ref_title = ask("text", "What is the name of the reference type?")
            ref_file = ask("text", "What is the name of the file within the reference?")
            elem["file"] = f"**/{ref_title}/**/{ref_file}"
        
        else:
            assert f"Internal error: prompt type not configured: {prompt_type}"

        # Map the form entry to the input params
        self.process_config["input"][kw] = f"{section_key}.{kw}"

        # Return the configuration of the parameter
        return kw, elem, required

    def _configure_inputs(self):
        """Configure any additional inputs."""

        if ask(
            "confirm",
            "Would you like to add any fixed parameter values?\n  These values will not change based on user input."
        ):

            self._add_fixed_param_input()

            while ask("confirm", "Would you like to add another?"):

                self._add_fixed_param_input()

    def _add_fixed_param_input(self):
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

            print(f"Internal error: parameter type {param_type} is not configured")

        # Let the user confirm their entry
        if ask("confirm", f"Confirm: {param_key} = {param_value}"):
            self.process_config["input"][param_key] = param_value

    def with_output(self):
        """Configure any additional outputs."""

        # Set up the blank output object
        commands = []
        self.process_config["output"] = dict(commands=commands)

        if ask(
            "confirm",
            "Does this workflow produce output files which should be indexed for visualization?"
        ):

            self._add_single_output()

            while ask("confirm", "Would you like to add another?"):

                self._add_single_output()
        return self

    def with_common_outputs(self):
        commands = self.process_config["output"]["commands"]

        # Add hot.Manifest if hot.Dsv is present
        if any(entry['command'] == 'hot.Dsv' for entry in commands):
            commands.append(
                {
                    "command": "hot.Manifest",
                    "params": {}
                }
            )

        # Add the commands to index all the files which were output
        commands.append(
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
        )
        return self

    def with_output(self):
        """Configure a single output file."""

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
                f"    {col['col']} - {col['name']} - {col['desc']}"
                for col in columns
            ] + [
                "Is all of the information above correct?"
            ])
        ):

            self.process_config["output"]["commands"].append(
                dict(
                    command="hot.Dsv",
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
