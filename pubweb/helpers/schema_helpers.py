import json

from github import Github
from github.GithubException import UnknownObjectException

from pubweb.cli.interactive.utils import ask


def get_nextflow_schema(repo: str, ref: str):
    """If a nextflow_schema.json is present, parse it and prompt the user for any modifications."""
    gh = Github()
    repo = gh.get_repo(repo)
    try:
        schema_file = repo.get_contents('nextflow_schema.json', ref)
        nf_schema = json.loads(schema_file.content)

        # Make sure that the schema has the expected top-level entries
        for k in ["title", "definitions"]:
            assert k in nf_schema, f"Did not find '{k}' in the nextflow schema as expected"

        return nf_schema
    except UnknownObjectException:
        print(f"No nextflow_schema.json file found, please specify any required inputs")
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
        assert "properties" in form_obj, f"Expected 'properties' when type='object':\n({json.dumps(form_obj, indent=4)})"

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
