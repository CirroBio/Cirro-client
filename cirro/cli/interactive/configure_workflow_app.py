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

        self.form = {"form": {}, "ui": {}}
        self.input = {}

        self.output = {
            "commands": [
                {
                    "command": "hot.Manifest",
                    "params": {}
                }
            ]
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
    def refresh_workflow_menu_ix(self):
        return st.session_state.get("refresh_workflow_menu_ix", 0)

    @refresh_workflow_menu_ix.setter
    def refresh_workflow_menu_ix(self, i: int):
        st.session_state["refresh_workflow_menu_ix"] = i

    def save(self):
        """Save all files to the folder."""
        for key_id, path, filetype in self.data_structure:
            self.save_file(key_id, self.folder / path, filetype)

    def save_file(self, attr, fp, filetype):
        """Write the JSON/text record to disk."""
        val = getattr(self, attr)
        assert val is not None, f"Could not find attribute {attr}"

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

        st.subheader('Workflow Description')

        # Set up an empty element to use for displaying the main workflow info
        self.workflow_empty = st.empty()

        # Display inputs for the parameters
        self.refresh_workflow_menu()

    def refresh_workflow_menu(self):

        # Replace any existing displays with an empty container
        self.refresh_workflow_menu_ix = self.refresh_workflow_menu_ix + 1
        self.workflow_container = self.workflow_empty.container()

        # Load the underlying data
        self.load()

        # When any of the following properties are set, the setter methods
        # will automatically save the changes to disk and refresh the app
        self.workflow_container.text_input(
            "Workflow Name",
            value=self.dynamo["name"],
            key=f"workflow.name.{self.refresh_workflow_menu_ix}",
            on_change=self.update_workflow_attribute,
            args=("name",)
        )
        self.workflow_container.text_input(
            "Workflow Description",
            value=self.dynamo["desc"],
            key=f"workflow.desc.{self.refresh_workflow_menu_ix}",
            on_change=self.update_workflow_attribute,
            args=("desc",)
        )
        self.workflow_container.radio(
            "Workflow Executor",
            ["Nextflow", "Cromwell"],
            ["Nextflow", "Cromwell"].index(self.dynamo["executor"].title()),
            key=f"workflow.executor.{self.refresh_workflow_menu_ix}",
            on_change=self.update_workflow_attribute,
            args=("executor",)
        )

    def update_workflow_attribute(self, attr):
        # Get the new value
        value = st.session_state[f"workflow.{attr}.{self.refresh_workflow_menu_ix}"]

        # The executor has special behavior
        if attr == "executor":
            # Must be all caps
            value = value.upper()

            # Must also be set in the computeDefaults
            self.dynamo["computeDefaults"][0]["executor"] = value

        # Set at the top level of the dynamo record
        if attr in self.dynamo:
            self.dynamo[attr] = value

        self.save()
        self.refresh_workflow_menu()

    def serve_parameter_info(self):
        """Allow the user to edit the set of parameters used for the workflow."""

        st.subheader('Workflow Parameters')

        # Set up an empty element to use for displaying the parameters
        self.parameter_empty = st.empty()

        # Display inputs for the parameters
        self.refresh_parameter_menu()

    def refresh_parameter_menu(self):
        """Populate the parameter configuration menu display."""

        # Remove the previous set of display elements
        # by replaceing the contents of self.parameter_empty with
        # an empty container
        self.refresh_parameter_menu_ix = self.refresh_parameter_menu_ix + 1
        self.parameter_container = self.parameter_empty.container()

        # Load any changed files
        self.load()

        # Keep track of the containers used for each parameter

        # Iterate over each of the parameters defined by the form
        for ix, parameter in enumerate(self.flatten_parameters()):

            expander = self.parameter_container.expander(
                f"Parameter: {parameter.get('title', ix + 1)}",
                expanded=True
            )

            # Display a set of menus to edit those parameters
            expander.text_input(
                "Parameter Display Name",
                **self.input_kwargs(parameter, "title")
            )
            expander.text_input(
                "Description",
                help="Longer description of the parameter",
                **self.input_kwargs(parameter, "description")
            )
            type_options = ["string", "boolean", "integer", "number"]
            expander.selectbox(
                "Variable Type",
                type_options,
                index=type_options.index(parameter["type"]),
                **self.input_kwargs(parameter, "type", omit=["value"])
            )
            expander.text_input(
                "Workflow Key",
                help="Keyword used to define the parameter for the workflow",
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
        elem = self.form['form']
        for v in path[:-1]:
            elem = elem[v]

        # Remove the indicated parameter
        del elem["properties"][path[-1]]

        # If there is a workflow_key defined, remove it
        while self.find_workflow_key(path) in self.input:
            del self.input[self.find_workflow_key(path)]

        self.save()

        # Redraw the entire input element
        self.refresh_parameter_menu()

    def update_parameter(self, path, attr):
        """Update an attribute of a given parameter."""

        # Get the new value
        val = st.session_state[".".join(path + [attr, str(self.refresh_parameter_menu_ix)])]

        # If the attribute is the workflow_key
        if attr == "workflow_key":

            # Get the previous key used for this element (if any)
            while self.find_workflow_key(path) is not None:
                del self.input[self.find_workflow_key(path)]
            self.input[val] = f"$.params.dataset.paramJson.{'.'.join(path)}"

        # Get the flat list of parameters, keyed by path
        flat_params = {
            ".".join(param["path"]): param
            for param in self.flatten_parameters()
        }

        # Modify the specified parameter
        flat_params['.'.join(path)][attr] = val

        # # Reform the nested set of parameters
        self.form["form"] = self.nest_parameters(flat_params)

        # Save the changes
        self.save()

        # Redraw the entire input element
        self.refresh_parameter_menu()

    def nest_parameters(self, flat):

        nested = dict(properties={})

        # Add all of the top-level parameters from flat
        for path, param in flat.items():

            # Turn the path into a list
            path = path.split(".")

            # Skip any nested
            if len(path) > 1:
                continue

            # Add it to the nested structure
            nested['properties'][param['workflow_key']] = {
                k: v
                for k, v in param.items()
                if k not in ["workflow_key", "path"]
            }

            # Find any parameters which are nested below this param
            sub_params = {
                k.split('.', 1)[1]: v
                for k, v in flat.items()
                if k.startswith(f"{param['workflow_key']}.")
            }

            if len(sub_params) > 0:
                nested[
                    'properties'
                ][
                    param['workflow_key']
                ][
                    'properties'
                ] = self.nest_parameters(
                    sub_params
                )

        return nested

    def flatten_parameters(self):

        # Recursively traverse the form elements
        for parameter in self.traverse_form(self.form["form"], []):
            yield parameter

    def traverse_form(self, form, root):

        for kw, val in form.get("properties", {}).items():

            param_path = root + [kw]

            workflow_key = self.find_workflow_key(param_path)
            if workflow_key is None:
                workflow_key = kw

            yield dict(
                path=param_path,
                type=val.get("type"),
                title=val.get("title"),
                description=val.get("description"),
                workflow_key=workflow_key
            )

            for elem in self.traverse_form(val, param_path):
                yield elem

    def find_workflow_key(self, param_path):
        """Check to see what key is used when passing this parameter to the workflow."""

        query_str = f"$.params.dataset.paramJson.{'.'.join(param_path)}"

        for kw, val in self.input.items():
            if val == query_str:
                return kw


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
