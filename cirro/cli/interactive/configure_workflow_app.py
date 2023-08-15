import io
import json
import threading
from time import sleep
from typing import List
from cirro import DataPortal
from cirro.api.auth.oauth_client import ClientAuth
from cirro.api.config import AppConfig
from cirro.api.clients.portal import DataPortalClient
from cirro.cli.interactive.upload_args import DataDirectoryValidator
from cirro.cli.interactive.utils import prompt_wrapper
from pathlib import Path
import pandas as pd
from prompt_toolkit.shortcuts import CompleteStyle
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.runtime.scriptrunner import script_run_context


def session_cache(func):
    def inner(*args, **kwargs):

        # Get the session context, which has a unique ID element
        ctx = get_script_run_ctx()

        # Define a cache key based on the function name and arguments
        cache_key = ".".join([
            str(ctx.session_id),
            func.__name__,
            ".".join(map(str, args)),
            ".".join([
                f"{k}={v}"
                for k, v in kwargs.items()
            ])
        ])

        # If the value has not been computed
        if st.session_state.get(cache_key) is None:
            # Compute it
            st.session_state[cache_key] = func(
                *args,
                **kwargs
            )

        # Return that value
        return st.session_state[cache_key]

    return inner


def cirro_login(login_empty):
    # If we have not logged in yet
    if st.session_state.get('DataPortal') is None:

        # Connect to Cirro - capturing the login URL
        auth_io = io.StringIO()
        cirro_login_thread = threading.Thread(
            target=cirro_login_sub,
            args=(auth_io,)
        )
        script_run_context.add_script_run_ctx(cirro_login_thread)

        cirro_login_thread.start()

        login_string = auth_io.getvalue()

        while len(login_string) == 0 and cirro_login_thread.is_alive():
            sleep(5)
            login_string = auth_io.getvalue()

        login_empty.write(login_string)
        cirro_login_thread.join()

    else:
        login_empty.empty()

    msg = "Error: Could not log in to Cirro"
    assert st.session_state.get('DataPortal') is not None, msg


def cirro_login_sub(auth_io: io.StringIO):

    app_config = AppConfig()

    st.session_state['DataPortal-auth_info'] = ClientAuth(
        region=app_config.region,
        client_id=app_config.client_id,
        auth_endpoint=app_config.auth_endpoint,
        enable_cache=False,
        auth_io=auth_io
    )

    st.session_state['DataPortal-client'] = DataPortalClient(
        auth_info=st.session_state['DataPortal-auth_info']
    )
    st.session_state['DataPortal'] = DataPortal(
        client=st.session_state['DataPortal-client']
    )


def list_datasets_in_project(project_name):

    # Connect to Cirro
    portal = st.session_state['DataPortal']

    # Access the project
    project = portal.get_project_by_name(project_name)

    # Get the list of datasets available (using their easily-readable names)
    return [""] + [ds.name for ds in project.list_datasets()]


@session_cache
def list_projects() -> List[str]:

    # Connect to Cirro
    portal = st.session_state['DataPortal']

    # List the projects available
    project_list = portal.list_projects()

    # Return the list of projects available (using their easily-readable names)
    return [proj.name for proj in project_list]


@session_cache
def get_dataset(project_name, dataset_name):
    """Return a Cirro Dataset object."""

    # Connect to Cirro
    portal = st.session_state['DataPortal']

    # Access the project
    project = portal.get_project_by_name(project_name)

    # Get the dataset
    return project.get_dataset_by_name(dataset_name)


@session_cache
def list_files_in_dataset(project_name, dataset_name):
    """Return a list of files in a dataset."""

    return [
        f.name
        for f in get_dataset(project_name, dataset_name).list_files()
    ]


@session_cache
def read_csv(project_name, dataset_name, fn, **kwargs):
    """Read a CSV from a dataset in Cirro."""

    return (
        get_dataset(project_name, dataset_name)
        .list_files()
        .get_by_name(f"data/{fn}")
        .read_csv(**kwargs)
    )


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
    def refresh_outputs_menu_ix(self):
        return st.session_state.get("refresh_outputs_menu_ix", 0)

    @refresh_outputs_menu_ix.setter
    def refresh_outputs_menu_ix(self, i: int):
        st.session_state["refresh_outputs_menu_ix"] = i

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
        cirro_login(st.empty())
        self.serve_workflow_info()
        self.serve_parameter_info()
        self.serve_outputs_info()

    ############
    # WORKFLOW #
    ############

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

    ##############
    # PARAMETERS #
    ##############

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

        # Iterate over each of the parameters defined by the form
        for ix, parameter in enumerate(self.flatten_parameters()):

            expander = self.parameter_container.expander(
                f"Parameter: {parameter.get('title', ix + 1)}",
                expanded=True
            )

            # Allow the user to set up a hard-coded vs. form-driven parameter
            expander.radio(
                "Parameter Type",
                ["User Input", "Hardcoded"],
                index=1 if parameter["hardcoded"] else 0,
                **self.input_kwargs(parameter, "hardcoded", omit=["value"])
            )

            if not parameter["hardcoded"]:

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
                print("here")
                print(parameter)
                expander.selectbox(
                    "Variable Type",
                    type_options,
                    index=type_options.index(parameter.get("type", "string")),
                    **self.input_kwargs(parameter, "type", omit=["value"])
                )

            expander.text_input(
                "Workflow Key",
                help="Keyword used to define the parameter for the workflow",
                **self.input_kwargs(parameter, "workflow_key")
            )

            expander.text_input(
                "Default Value",
                help="Value assigned to the parameter by default",
                **self.input_kwargs(parameter, "default")
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
        elem = self.form['form']
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
        self.input[key] = f"$.params.dataset.paramJson.{'.'.join(path + [key])}"

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

        # Get the flat list of parameters, keyed by path
        flat_params = {
            ".".join(param["path"]): param
            for param in self.flatten_parameters()
        }

        # Get the state of the parameter, prior to being modified
        param = flat_params[".".join(path)]

        # Get the workflow key
        workflow_key = param.get("workflow_key")

        # Get the form element to modify
        elem = self.form['form']
        for v in path[:-1]:
            elem = elem[v]

        # Remove the indicated parameter
        if path[-1] in elem["properties"]:
            del elem["properties"][path[-1]]

        # If there is a workflow_key defined, remove it
        while self.find_workflow_key(path) in self.input:
            del self.input[self.find_workflow_key(path)]

        # If there is a workflow key defined
        if workflow_key is not None:
            if workflow_key in self.input:
                del self.input[workflow_key]

        self.save()

        # Redraw the entire input element
        self.refresh_parameter_menu()

    def update_parameter(self, path, attr):
        """Update an attribute of a given parameter."""

        # Get the new value
        val = st.session_state[".".join(path + [attr, str(self.refresh_parameter_menu_ix)])]

        # Get the flat list of parameters, keyed by path
        flat_params = {
            ".".join(param["path"]): param
            for param in self.flatten_parameters()
        }

        # Get the state of the parameter, prior to being modified
        param = flat_params[".".join(path)]

        # If we are modifying the "hardcoded" attribute
        if attr == "hardcoded":
            # Transform the value to a 1/0
            val = val == "Hardcoded"

        print("HERE")
        print(path)
        print(attr)
        print(val)
        print(param)
        print("HERE2")

        # If this is a hardcoded parameter and we're not changing that attribute
        if param["hardcoded"] and attr != "hardcoded":

            # If the attribute is the workflow_key
            if attr == "workflow_key":

                # Set up the newly indicated key
                self.input[val] = self.input[param["workflow_key"]]
                del self.input[param["workflow_key"]]

            # If the modified attribute is the value
            elif attr == "default":

                # Modify the default value
                self.input[param["workflow_key"]] = val

            else:
                raise Exception(f"Did not expect attribute: {attr}")

        # If this is a form-driven parameter
        else:

            # If the attribute is the workflow_key
            if attr == "workflow_key":

                # Get the previous key used for this element (if any)
                while self.find_workflow_key(path) is not None:
                    del self.input[self.find_workflow_key(path)]
                self.input[val] = f"$.params.dataset.paramJson.{'.'.join(path)}"

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

            # Hardcoded parameters do not go into the form
            if param["hardcoded"]:
                continue

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

        # Keep track of parameters which are defined in the form
        form_parameters = set([])

        # Recursively traverse the form elements
        for parameter in self.traverse_form(self.form["form"], []):
            form_parameters.add(parameter["workflow_key"])
            yield parameter

        # Iterate over the inputs, to find the hardcoded parameters
        for kw, val in self.input.items():
            # If the parameter is not defined in the form, it must be hardcoded
            if kw not in form_parameters:
                yield dict(
                    hardcoded=1,
                    workflow_key=kw,
                    default=val,
                    path=[kw]
                )

    def traverse_form(self, form, root):

        for kw, val in form.get("properties", {}).items():

            param_path = root + [kw]

            workflow_key = self.find_workflow_key(param_path)
            if workflow_key is None:
                workflow_key = kw

            yield dict(
                hardcoded=0,
                path=param_path,
                type=val.get("type", "string"),
                title=val.get("title"),
                description=val.get("description"),
                default=val.get("default"),
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

    ###########
    # OUTPUTS #
    ###########

    def serve_outputs_info(self):
        """Display the editable interface for workflow outputs."""

        st.subheader('Workflow Output Files')

        # Set up an empty element to use for loading example data from Cirro
        self.outputs_template = st.empty()
        self.load_output_template_from_cirro()

        # Set up an empty element to use for displaying the outputs info
        self.outputs_empty = st.empty()

        # Display inputs for the parameters
        self.refresh_outputs_menu()

    def load_output_template_from_cirro(self):
        """Load a set of example data from Cirro."""

        outputs_template_container = self.outputs_template.expander(
            "Load Template Dataset (Cirro)",
            expanded=False
        )

        selected_project = outputs_template_container.selectbox(
            "Select Project",
            [""] + list_projects()
        )

        if selected_project == "":
            return

        selected_dataset = outputs_template_container.selectbox(
            "Select Dataset",
            [""] + list_datasets_in_project(selected_project)
        )

        if selected_dataset == "":
            return

        # TODO
        file_list = list_files_in_dataset(selected_project, selected_dataset)


    def refresh_outputs_menu(self):

        # Replace any existing displays with an empty container
        self.refresh_outputs_menu_ix = self.refresh_outputs_menu_ix + 1
        self.outputs_container = self.outputs_empty.container()

        # Load any changed files
        self.load()

        # Iterate over each of the outputs defined by the workflow
        for ix, command in enumerate(self.output.get('commands', [])):

            # Skip the manifest command
            if command['command'] == "hot.Manifest":
                continue

            # Only the hot.Dsv command is supported
            msg = f"Command not supported: {command['command']}"
            assert command['command'] == "hot.Dsv", msg

            # Nest all of the menu items in an expander
            expander = self.outputs_container.expander(
                f"Output {ix}",
                expanded=True
            )
            # Display a set of menus for this output
            expander.text_input(
                "File Name",
                **self.output_kwargs(command["params"], ix, "name")
            )
            expander.text_input(
                "File Description",
                **self.output_kwargs(command["params"], ix, "desc")
            )
            expander.text_input(
                "Documentation URL",
                **self.output_kwargs(command["params"], ix, "url")
            )
            expander.radio(
                "File Contains Header",
                [True, False],
                [True, False].index(command["params"]["header"]),
                **self.output_kwargs(command["params"], ix, "header", omit=["value"])
            )
            expander.selectbox(
                "Delimiter",
                [",", "\\t"],
                [",", "\t"].index(command["params"]["sep"]),
                **self.output_kwargs(command["params"], ix, "sep", omit=["value"])
            )
            expander.text_input(
                "Relative Path in Output Directory",
                **self.output_kwargs(command["params"], ix, "source")
            )
            self.prompt_file_columns(expander, ix)

            # Button used to remove an output file
            self.remove_output_button(expander, ix)

        # Add a button to add a new output element
        self.add_output_button()

    def remove_output_button(self, expander, ix):
        expander.button(
            "Remove Output File",
            on_click=self.remove_output,
            args=(ix,),
            key=f"remove_output.{ix}" + f"-{self.refresh_outputs_menu_ix}"
        )

    def remove_output(self, ix):
        self.output["commands"].pop(ix)
        self.save()
        self.refresh_outputs_menu()

    def output_kwargs(self, params, ix, attr, omit=[]):
        """Return a set of kwargs used for a streamlit UI element."""

        return {
            kw: val for kw, val in dict(
                on_change=self.update_output,
                value=params.get(attr, ""),
                args=(ix, attr,),
                key=f"_outputs.{ix}" + f".{attr}.{self.refresh_outputs_menu_ix}"
            ).items()
            if kw not in omit
        }

    def update_output(self, ix, attr):
        """Change the value of an outputs element."""

        # Get the new value
        val = st.session_state[f"_outputs.{ix}" + f".{attr}.{self.refresh_outputs_menu_ix}"]

        # Special case some of the attributes
        if attr == "sep":
            if val == "\\t":
                val = "\t"

        # Change the indicated output element
        self.output["commands"][ix]["params"][attr] = val

        self.save()
        self.refresh_outputs_menu()

    def prompt_file_columns(self, expander, ix):
        """Display a set of prompts for the columns in a file"""

        # Iterate over the columns defined for this file
        for col_ix, col in enumerate(self.output["commands"][ix]["params"]["cols"]):

            # Put the column elements in a set of columns
            cols = expander.columns(3)

            cols[0].text_input(
                "Column Header",
                **self.prompt_file_columns_kwargs(ix, col_ix, col, "col")
            )
            cols[1].text_input(
                "Column Name",
                **self.prompt_file_columns_kwargs(ix, col_ix, col, "name")
            )
            cols[2].text_area(
                "Column Description",
                **self.prompt_file_columns_kwargs(ix, col_ix, col, "desc")
            )
            expander.button(
                "Remove Column",
                on_click=self.remove_output_column,
                args=(ix, col_ix,),
                key=f"remove_output_column.{ix}.{col_ix}.{self.refresh_outputs_menu_ix}"
            )
        expander.button(
            "Add Column",
            on_click=self.add_output_column,
            args=(ix, ),
            key=f"add_output_column.{ix}.{self.refresh_outputs_menu_ix}"
        )

    def remove_output_column(self, ix, col_ix):

        # Delete the output column
        self.output["commands"][ix]["params"]["cols"].pop(col_ix)

        # Refresh the app
        self.save()
        self.refresh_outputs_menu()

    def add_output_column(self, ix):
        """Add an output column."""
        self.output["commands"][ix]["params"]["cols"].append(
            dict(
                col="",
                name="",
                desc=""
            )
        )

        # Refresh the app
        self.save()
        self.refresh_outputs_menu()

    def prompt_file_columns_kwargs(self, ix, col_ix, col, attr):

        return dict(
            value=col[attr],
            on_change=self.update_output_column,
            args=(ix, col_ix, attr,),
            key=f"output_{ix}.col_{col_ix}.{attr}.{self.refresh_outputs_menu_ix}"
        )

    def update_output_column(self, output_ix, col_ix, col_attr):

        # Get the value
        val = st.session_state[
            f"output_{output_ix}.col_{col_ix}.{col_attr}.{self.refresh_outputs_menu_ix}"
        ]

        # Update the corresponding element
        self.output["commands"][output_ix]["params"]["cols"][col_ix][col_attr] = val
        self.save()
        self.refresh_outputs_menu()

    def add_output_button(self):

        self.outputs_container.button(
            "Add Output File (Manual)",
            on_click=self.add_output,
            key=f"add_output.{self.refresh_parameter_menu_ix}"
        )

        self.outputs_container.file_uploader(
            "Add Output File (From Example)",
            on_change=self.add_output_template,
            key=f"add_output_template.{self.refresh_parameter_menu_ix}"
        )

    def add_output_template(self):
        # Get the file that was uploaded
        file = st.session_state[
            f"add_output_template.{self.refresh_parameter_menu_ix}"
        ]

        # Read as CSV
        if "tsv" in file.name:
            sep = "\t"
            df = pd.read_excel(file, sep="\t")
        else:
            sep = ","
            df = pd.read_csv(file)

        # Add the columns to the output
        self.output["commands"].append(
            {
                "command": "hot.Dsv",
                "params": {
                    "url": "",
                    "source": "",
                    "filename": file.name,
                    "sep": sep,
                    "header": True,
                    "name": file.name,
                    "desc": "",
                    "cols": [
                        dict(
                            col=cname,
                            name=cname,
                            desc=""
                        )
                        for cname in df.columns.values
                    ]
                }
            }
        )
        self.save()
        self.refresh_outputs_menu()

    def add_output(self):

        self.output["commands"].append(dict(
            command="hot.Dsv",
            params=dict(
                url="",
                source="",
                filename="",
                sep=",",
                header=True,
                name="Output file name",
                desc="Output file description",
                cols=[]
            )
        ))

        self.save()
        self.refresh_outputs_menu()

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
