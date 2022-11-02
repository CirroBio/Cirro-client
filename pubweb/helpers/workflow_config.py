import json
import shutil
from pathlib import Path
from typing import List, Dict

from pubweb.helpers.constants import PROCESSES_PATH_S3
from pubweb.api.models.process import ProcessRecord, Executor
from pubweb.api.models.workflow_models import OptimizedOutput, WorkflowRepository, ProcessConfig


class WorkflowConfigBuilder:
    def __init__(self, repo_prefix: str):
        """
        Initializes workflow config builder
        :param repo_prefix: subdirectory to write to (i.e. hutch/fastqc/1.0
        """

        # All the parameters will be added to a single object
        self.process_config = ProcessConfig(
            dynamo=dict(),
            form=dict(),
            input=dict(),
            output=dict()
        )
        self.repo_prefix = repo_prefix.strip('/')
        self.compute_config = ""
        self.preprocess_py_path = None

        # Set up the boilerplate elements of the dynamo record
        self._add_dynamo_boilerplate()

    def save_local(self, output_folder: Path):
        """
        Write out the workflow configuration as a collection of files.
        """
        output_folder.mkdir(parents=True, exist_ok=True)

        # Reorder dynamo config based on model order
        ordered_record = {}
        for key in ProcessRecord.__annotations__.keys():
            value = self.process_config["dynamo"].get(key)  # type: ignore
            if value is not None:
                ordered_record[key] = value
        self.process_config["dynamo"] = ordered_record

        # Save each of the items in the process configuration
        for config_name, config_value in self.process_config.items():
            output_fp = Path(output_folder, f"process-{config_name}.json")
            print(f"Writing out to {output_fp}")

            with output_fp.open('w') as handle:
                json.dump(config_value, handle, indent=4)

        # Write the compute configuration
        compute_path = Path(output_folder, "process-compute.config")
        print(f"Boilerplate compute configuration has been written to {compute_path}"
              f" -- please modify that file as necessary.")

        with compute_path.open("w") as handle:
            handle.write(self.compute_config)

        # Copy preprocess file
        if self.preprocess_py_path is not None:
            preprocess_dest = Path(output_folder, self.preprocess_py_path.name)
            print(f"Copying preprocess from {self.preprocess_py_path} to {preprocess_dest}")
            shutil.copyfile(
                self.preprocess_py_path,
                preprocess_dest
            )
        print(f"Done writing all process configuration items to {output_folder}")

    def with_description(self, description: str):
        self.process_config["dynamo"]["desc"] = description
        return self

    def with_repository(self, repo: WorkflowRepository):
        """
        Configure the workflow repository.
        """

        # Get the name of the process
        self.process_config["dynamo"]["name"] = repo.display_name

        # Set up the process name based on the workflow/version
        process_id = f"process-{repo.org}-{repo.repo_name}-{repo.version}".lower()
        self.process_config["dynamo"]["id"] = process_id

        repository_code = f"GITHUB{'PRIVATE' if repo.private else 'PUBLIC'}"
        # Set up the 'code' block of the dynamo record
        self.process_config["dynamo"]["code"] = dict(
            repository=repository_code,
            script=repo.entrypoint,
            uri=f"{repo.org}/{repo.repo_name}",
            version=repo.version
        )
        self.process_config["dynamo"]["documentationUrl"] = repo.documentation_url

        return self

    def with_child_processes(self, child_processes: List[str]):
        """
        Specify what child processes are allowed to run from the output of this dataset
        """
        self.process_config["dynamo"]["childProcessIds"] = child_processes

        return self

    def with_preprocess(self, preprocess_py_path: Path):
        """
        Add a preprocess file
        """
        # Add it to the dynamo record
        self.process_config["dynamo"]["preProcessScript"] = \
            f"{PROCESSES_PATH_S3}/{self.repo_prefix}/{preprocess_py_path.name}"
        self.preprocess_py_path = preprocess_py_path

        return self

    def _add_dynamo_boilerplate(self):
        """
        Add the elements of the dynamo record which do not vary by user entry.
        """

        self.process_config["dynamo"]["executor"] = Executor.NEXTFLOW.value
        self.process_config["dynamo"]["paramDefaults"] = []
        self.process_config["dynamo"]["fileJson"] = ""
        self.process_config["dynamo"]["componentJson"] = ""
        self.process_config["dynamo"]["infoJson"] = ""
        self.process_config["dynamo"]["paramMapJson"] = \
            f"{PROCESSES_PATH_S3}/{self.repo_prefix}/process-input.json"
        self.process_config["dynamo"]["formJson"] = \
            f"{PROCESSES_PATH_S3}/{self.repo_prefix}/process-form.json"
        self.process_config["dynamo"]["webOptimizationJson"] = \
            f"{PROCESSES_PATH_S3}/{self.repo_prefix}/process-output.json"

    def with_compute(self, max_retries=2):
        """
        Configure the compute configuration.
        The compute configuration is boilerplate at this point
        """

        self.process_config["dynamo"]["computeDefaults"] = [
            {
                "executor": "NEXTFLOW",
                "json": f"{PROCESSES_PATH_S3}/{self.repo_prefix}/process-compute.config",
                "name": "Default"
            }
        ]

        self.compute_config = f"""profiles {{
    standard {{
        process {{
            executor = 'awsbatch'
            errorStrategy = 'retry'
            maxRetries = {max_retries}
        }}
    }}
}}
"""
        return self

    def with_form_inputs(self, form):
        """
        Configure the form. UI customizations not supported yet.
        """
        # TODO This could be improved to take a list of form objects
        #  instead of a json schema

        self.process_config["form"] = dict(
            ui=dict(),
            # In addition to modifying the schema contents, we will
            # also ask the user if they want to include or exclude each option
            form=form
        )
        return self

    def with_inputs(self, inputs: Dict[str, str]):
        """
        Configure multiple inputs
        """
        self.process_config["input"] = {
            **self.process_config["input"],
            **inputs
        }
        return self

    def with_input(self, input_name: str, input_value: str):
        """
        Configure a single input parameter mapping
        """
        self.process_config["input"][input_name] = input_value
        return self

    def with_output(self, output: OptimizedOutput):
        """
        Configure a single output file.
        """
        self._init_outputs()
        self.process_config["output"]["commands"].append(
            dict(
                command="hot.Dsv",
                params=dict(
                    url=output.documentation_url,
                    source=output.source_pattern,
                    sep=output.seperator,
                    header=True,
                    name=output.name,
                    desc=output.description,
                    cols=[
                        {
                            'col': col.header,
                            'name': col.display_name,
                            'desc': col.description
                        }
                        for col in output.columns
                    ]
                )
            )
        )
        return self

    def with_common_outputs(self):
        self._init_outputs()
        commands = self.process_config["output"]["commands"]

        # Add hot.Manifest if hot.Dsv is present
        if any(entry['command'] == 'hot.Dsv' for entry in commands):
            # Add the command to index datasources that are present
            commands.append(
                {
                    "command": "hot.Manifest",
                    "params": {}
                }
            )

        # Add the command to index all the files which were outputted
        commands.append(
            {
                "command": "save.ManifestJson",
                "params": {
                    "files": [
                        {
                            "glob": "$data_directory/**/*.*"
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

    def _init_outputs(self):
        """Checks if we need to initialize the blank output"""
        if not self.process_config["output"]:
            self.process_config["output"] = dict(commands=[])
            self.process_config["dynamo"]["webOptimizationJson"] = \
                f"{PROCESSES_PATH_S3}/{self.repo_prefix}/process-output.json"
