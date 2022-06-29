import json

from github import UnknownObjectException, Github

from pubweb.cli.interactive.utils import ask, ask_yes_no
from pubweb.helpers.constants import IGENOMES_REFERENCES


def prompt_user_inputs():
    """Prompt for user inputs which should be included in the form."""

    # Make a dict with the properties which should be rendered in the form
    # Each parameter will fall inside a section with its own title
    properties = dict()
    inputs = dict()

    print("The form which is presented to the user is broken into sections, each with its own heading")

    while len(properties) == 0 or ask("confirm", "Would you like to add another section of parameters?"):
        # Get the contents of this section
        section_key, section_contents = _prompt_user_input_section(inputs)

        # Add those contents to the form
        properties[section_key] = section_contents

    return properties, inputs


def _prompt_user_input_section(inputs):
    """Ask the user for all of the parameters which are found in a single section of the input form."""

    section_title = ask("text", "What is the title of this section?")

    # Format the section key based on the title
    section_key = section_title.lower().replace(" ", "_").replace("-", "_")

    # Build a dict of the individual form entries
    properties = dict()

    # Keep track of which inputs are required
    required = []

    for input_key, input_val, input_required in _yield_form_input_single(inputs, section_key):

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


def _yield_form_input_single(inputs, section_key):
    """Allow the user to add as many form inputs as they require."""

    initial = True

    while initial or ask("confirm", "Would you like to add another parameter to this section?"):
        initial = False

        yield _prompt_form_input_single(inputs, section_key)


def _prompt_form_input_single(inputs, section_key):
    """Prompt the user for a single element in the form."""

    # Prompt for the parameter key
    kw = ask("text", "Parameter key used in workflow:")

    # There should be no collision between keys
    while len(kw) == 0 or kw in inputs:
        kw = ask("text", "Parameter key is not valid or has already been used, please select another:")

    elem = dict()
    elem["title"] = ask("text", "Parameter title (optional)")
    elem["description"] = ask("text", "Parameter description:")
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
    inputs[kw] = f"{section_key}.{kw}"

    # Return the configuration of the parameter
    return kw, elem, required


def get_nextflow_schema(repo: str, ref: str):
    """If a nextflow_schema.json is present, parse it and prompt the user for any modifications."""
    gh = Github()
    repo = gh.get_repo(repo)
    try:
        schema_file = repo.get_contents('nextflow_schema.json', ref)
        nf_schema = json.loads(schema_file.decoded_content)

        # Make sure that the schema has the expected top-level entries
        for k in ["title", "definitions"]:
            assert k in nf_schema, f"Did not find '{k}' in the nextflow schema as expected"

        return nf_schema
    except UnknownObjectException:
        print("No nextflow_schema.json file found, please specify any required inputs")
        return None


def convert_nf_schema(form_obj, inputs, param_root="$.params.dataset.paramJson"):
    """
    Given a nextflow schema object, parse it and
    run the user through prompts to determine which fields to expose
    """

    # Remove any unwanted keys
    for k in ["$schema", "$id", "fa_icon", "mimetype", "allOf", "schema"]:
        if k in form_obj:
            del form_obj[k]

    # Convert the 'definitions' from the Nextflow schema to 'properties' of the form
    if "definitions" in form_obj:
        form_obj["properties"] = form_obj["definitions"]
        del form_obj["definitions"]

    # The object should have a "type"
    assert "type" in form_obj, f"Expected 'type':\n({json.dumps(form_obj, indent=4)})"

    # If this is an object
    if form_obj["type"] == "object":

        # It must have "properties"
        assert "properties" in form_obj, f"Expected 'properties' when type='object':\n" \
                                         f"({json.dumps(form_obj, indent=4)})"

        # Give the user the option to remove items from that list

        # First ask the user which options should be kept
        option_list = [
            f"{k}\n     {v.get('description')}"
            for k, v in form_obj["properties"].items()
        ]
        to_keep = ask(
            "checkbox",
            "Please select the items to display to the user\n<space> to select/deselect, <enter> when done",
            choices=option_list
        )

        # Remove the description from the list of
        to_keep = [i.split("\n")[0] for i in to_keep]

        # Subset the defs to only keep the selected options
        form_obj["properties"] = {
            k: form_obj["properties"][k]
            for k in to_keep
        }

        # If there is a "required" field at the top level
        if "required" in form_obj:
            # Only keep the required items which were selected
            form_obj["required"] = [i for i in form_obj["required"] if i in to_keep]

        # Now convert each of those objects in a recursive way
        form_obj["properties"] = {
            k: convert_nf_schema(v, param_root=f"{param_root}.{k}", inputs=inputs)
            for k, v in form_obj["properties"].items()
        }

        # For each of those elements
        for k, v in form_obj["properties"].items():

            # Skip any other objects
            if v["type"] == "object":
                continue

            # Any other type needs to be added to the inputs

            # Make sure that this parameter name doesn't collide with anything else
            assert k not in inputs, f"Error, found two elements in the form named {k}"

            # Add it to the inputs
            inputs[k] = f"{param_root}.{k}"

    # Return the object
    return form_obj
