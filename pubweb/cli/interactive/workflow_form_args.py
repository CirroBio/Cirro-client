from pubweb.cli.interactive.utils import ask, ask_yes_no
from pubweb.helpers.constants import IGENOMES_REFERENCES


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
