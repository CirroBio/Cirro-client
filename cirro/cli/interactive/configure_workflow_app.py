import json
from cirro.api.clients.portal import DataPortalClient
from cirro.cli.interactive.upload_args import DataDirectoryValidator
from cirro.cli.interactive.utils import prompt_wrapper
from pathlib import Path
from prompt_toolkit.shortcuts import CompleteStyle
import streamlit as st


class WorkflowConfig:
    """Workflow configuration object."""

    def __init__(self, folder="."):

        ###################
        # SET UP DEFAULTS #
        ###################

        self.dynamo = {
            "id": "",
            "childProcessIds": [],
            "name": "",
            "desc": "",
            "executor": "NEXTFLOW",
            "documentationUrl": "",
            "code": {
                "repository": "GITHUBPUBLIC",
                "script": "main.nf",
                "uri": "",
                "version": ""
            },
            "paramDefaults": [],
            "computeDefaults": [
                {
                    "executor": "NEXTFLOW",
                    "json": "s3://<RESOURCES_BUCKET>/<PROCESS_DIRECTORY>/process-compute.config",
                    "name": "Default"
                }
            ],
            "paramMapJson": "s3://<RESOURCES_BUCKET>/<PROCESS_DIRECTORY>/process-input.json",
            "preProcessScript": "s3://<RESOURCES_BUCKET>/<PROCESS_DIRECTORY>/preprocess.py",
            "formJson": "s3://<RESOURCES_BUCKET>/<PROCESS_DIRECTORY>/process-form.json",
            "fileJson": "",
            "componentJson": "",
            "infoJson": "",
            "webOptimizationJson": "s3://<RESOURCES_BUCKET>/<PROCESS_DIRECTORY>/process-output.json"
        }

        self.compute = "// Empty compute config"
        self.preprocess = ""

        ##############
        # LOAD FILES #
        ##############

        self.folder = Path(folder)
        self.data_structure = [
            ("dynamo", "process-dynamo.json", "json"),
            ("compute", "process-compute.config", "text"),
            ("preprocess", "preprocess.py", "json"),
            ("form", "process-form.json", "json"),
            ("input", "process-input.json", "json"),
            ("output", "process-output.json", "json")
        ]
        self.load()

    @property
    def refresh_parameter_menu_ix(self):
        return st.session_state.get("refresh_parameter_menu_ix", 0)

    @refresh_parameter_menu_ix.setter
    def refresh_parameter_menu_ix(self, i: int):
        st.session_state["refresh_parameter_menu_ix"] = i

    @property
    def form(self):

        return st.session_state.get(
            "_form",
            {"form": {}, "ui": {}}
        )

    @form.setter
    def form(self, form):
        st.session_state["_form"] = form

    @property
    def input(self):

        return st.session_state.get("_input", {})

    @input.setter
    def input(self, input):
        st.session_state["_input"] = input

    @property
    def output(self):

        return st.session_state.get(
            "_output",
            {
                "commands": [
                    {
                        "command": "hot.Manifest",
                        "params": {}
                    }
                ]
            }
        )

    @output.setter
    def output(self, output):
        st.session_state["_output"] = output

    def save(self):
        """Save all files to the folder."""
        for key_id, path, filetype in self.data_structure:
            self.save_file(key_id, self.folder / path, filetype)

    def save_file(self, attr, fp, filetype):
        """Write the JSON/text record to disk."""
        val = getattr(self, attr)
        if val is None:
            print(f"Skipping {attr}")
            return

        if filetype == "json":
            write_json(val, fp)
        elif filetype == "text":
            write_text(val, fp)
        else:
            raise Exception(f"filetype not recognized: {filetype}")

    def load(self):
        """Load all files from the folder."""
        for key_id, path, filetype in self.data_structure:
            self.load_file(key_id, self.folder / path, filetype)

    def load_file(self, attr, fp, filetype):
        """Read the JSON/text record."""
        if fp.exists():
            if filetype == "json":
                setattr(self, attr, read_json(fp))
            elif filetype == "text":
                setattr(self, attr, read_text(fp))
            else:
                raise Exception(f"filetype not recognized: {filetype}")

    def serve(self):
        """Launch an interactive display allowing the user to configure the workflow."""

        st.set_page_config(
            page_title="Cirro - Workflow Configuration",
            page_icon="https://cirro.bio/favicon-32x32.png"
        )
        st.header("Cirro - Workflow Configuration")
        self.serve_workflow_info()
        self.serve_parameter_info()

    def serve_workflow_info(self):
        """Allow the user to edit general information about the workflow."""

        self.long_name = st.text_input("Workflow Name", value=self.long_name)
        self.description = st.text_input("Workflow Description", value=self.description)
        self.executor = st.radio(
            "Workflow Executor",
            ["Nextflow", "Cromwell"],
            ["Nextflow", "Cromwell"].index(self.executor.title())
        )

    def serve_parameter_info(self):
        """Allow the user to edit the set of parameters used for the workflow."""

        # Set up an empty element to use for displaying the parameters
        self.parameter_empty = st.empty()

        # Display inputs for the parameters
        self.refresh_parameter_menu()

    def refresh_parameter_menu(self):
        """Populate the parameter configuration menu display."""

        # Remove the previous set of display elements
        self.refresh_parameter_menu_ix = self.refresh_parameter_menu_ix + 1
        self.parameter_container = self.parameter_empty.container()

        # Keep track of the containers used for each parameter

        # Iterate over each of the parameters defined by the form
        for ix, parameter in enumerate(self.list_parameters()):

            expander = self.parameter_container.expander(
                f"Parameter {ix + 1}",
                expanded=True
            )

            # Display a set of menus to edit those parameters
            expander.text_input(
                "Parameter Name",
                **self.input_kwargs(parameter, "title")
            )
            expander.text_input(
                "Description",
                **self.input_kwargs(parameter, "description")
            )
            expander.selectbox(
                "Variable Type",
                ["string", "boolean", "integer", "number"],
                **self.input_kwargs(parameter, "type", omit=["value"])
            )
            expander.text_input(
                "Workflow Key",
                **self.input_kwargs(parameter, "workflow_key")
            )

            # Add a button to delete the parameter
            self.remove_parameter_button(expander, parameter["path"])

        # Add a button to add a new element to the root
        self.add_parameter_button([])

    def input_kwargs(self, parameter, attr, omit=[]):

        return {
            kw: val for kw, val in dict(
                on_change=self.update_parameter,
                value=parameter.get(attr, ""),
                args=(parameter["path"], attr,),
                key='.'.join(parameter["path"]) + f".{attr}.{self.refresh_parameter_menu_ix}"
            ).items()
            if kw not in omit
        }

    def add_parameter_button(self, path):

        self.parameter_container.button(
            "Add Parameter",
            on_click=self.add_parameter,
            args=(path,),
            key=f"add_parameter.{'.'.join(path)}" + f"-{self.refresh_parameter_menu_ix}"
        )

    def add_parameter(self, path):

        # Get the form element to modify
        form = self.form
        elem = form['form']
        for v in path:
            elem = elem[v]

        # If there are no properties defined
        if "properties" not in elem:
            # Add an empty dict
            elem["properties"] = {}

        # Find an unused key
        i = 0
        key = f"param_{i+1}"
        while key in elem["properties"] or key in self.input:
            i += 1
            key = f"param_{i+1}"

        # Add to the form JSON
        elem["properties"][key] = dict(
            type="string",
            title=f"Parameter {i + 1}",
            description=""
        )

        # Add to the inputs JSON
        input = self.input
        input[key] = f"$.params.dataset.paramJson.{'.'.join(path + [key])}"

        self.input = input
        self.form = form
        self.save()

        # Redraw the entire input element
        self.refresh_parameter_menu()

    def remove_parameter_button(self, expander, path):

        expander.button(
            "Remove Parameter",
            on_click=self.remove_parameter,
            args=(path,),
            key=f"remove_parameter.{'.'.join(path)}" + f"-{self.refresh_parameter_menu_ix}"
        )

    def remove_parameter(self, path):

        # Get the form element to modify
        form = self.form
        elem = form['form']
        for v in path[:-1]:
            elem = elem[v]

        # Remove the indicated parameter
        del elem["properties"][path[-1]]
        self.form = form

        # If there is a workflow_key defined, remove it
        workflow_key = self.find_workflow_key(".".join(path))
        if workflow_key in self.input:
            input = self.input
            del input[workflow_key]
            self.input = input

        self.save()

        # Redraw the entire input element
        self.refresh_parameter_menu()

    def update_parameter(self, path, attr):
        """Update an attribute of a given parameter."""

        # Get the new value
        val = st.session_state[".".join(path + [attr, str(self.refresh_parameter_menu_ix)])]

        # If the attribute is the workflow_key
        if attr == "workflow_key":

            # Modify the inputs element
            input = self.input

            # Get the previous key used for this element (if any)
            previous_key = self.find_workflow_key(path)
            if previous_key is not None:
                del input[previous_key]
            input[val] = f"$.params.dataset.paramJson.{'.'.join(path)}"
            self.input = input

        else:

            # Get the form element to modify
            form = self.form
            elem = form['form']
            for key in path:
                elem = elem["properties"][key]

            # Set the attribute
            elem[attr] = val
            self.form = form

        # Save the changes
        self.save()

        # Redraw the entire input element
        self.refresh_parameter_menu()

    def list_parameters(self):

        # Recursively traverse the form elements
        for parameter in self.traverse_form(self.form["form"], []):
            yield parameter

    def traverse_form(self, form, root):

        for kw, val in form.get("properties", {}).items():

            param_path = root + [kw]

            yield dict(
                path=param_path,
                type=val.get("type"),
                title=val.get("title"),
                description=val.get("description"),
                workflow_key=self.find_workflow_key(param_path)
            )

            for elem in self.traverse_form(val, param_path):
                yield elem

    def find_workflow_key(self, param_path):
        """Check to see what key is used when passing this parameter to the workflow."""

        query_str = f"$.params.dataset.paramJson.{'.'.join(param_path)}"

        for kw, val in self.input.items():
            if val == query_str:
                return kw

    @property
    def long_name(self):
        """Human-readable name for the workflow."""
        return self.dynamo["name"]

    @long_name.setter
    def long_name(self, value: str):
        self.dynamo["name"] = value
        self.dynamo["id"] = value.lower().strip().replace(" ", "-")
        self.save()

    @property
    def description(self):
        """Longer description of the workflow."""
        return self.dynamo["desc"]

    @description.setter
    def description(self, value):
        self.dynamo["desc"] = value
        self.save()

    @property
    def executor(self):
        """Workflow executor."""
        return self.dynamo["executor"].title()

    @executor.setter
    def executor(self, value):
        self.dynamo["executor"] = value.upper()
        self.save()


def read_json(fp) -> dict:
    with open(fp, "rt") as handle:
        return json.load(handle)


def write_json(dat, fp, indent=4, **kwargs) -> None:
    with open(fp, "wt") as handle:
        json.dump(dat, handle, indent=indent, **kwargs)


def read_text(fp) -> str:
    with open(fp, "rt") as handle:
        return handle.read()


def write_text(text, fp) -> None:
    with open(fp, "wt") as handle:
        handle.write(text)


def ask_workflow_directory(input_value: str) -> str:
    directory_prompt = {
        'type': 'path',
        'name': 'folder',
        'message': 'Folder used for workflow configuration files',
        'validate': DataDirectoryValidator,
        'default': input_value,
        'complete_style': CompleteStyle.READLINE_LIKE,
        'only_directories': True
    }

    answers = prompt_wrapper(directory_prompt)
    return answers['folder']


def configure_workflow_app():
    """Launch an interactive interface for configuring a workflow."""

    # Create a configuration object, loading any files that are already present
    config = WorkflowConfig()

    # Launch an interactive display allowing the user to modify
    # the workflow configuration
    config.serve()


if __name__ == "__main__":
    configure_workflow_app()
