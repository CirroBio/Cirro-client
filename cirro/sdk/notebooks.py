from functools import lru_cache
import json
from pathlib import Path
import re

from typing import Any
from cirro import DataPortal
from cirro.sdk.dataset import DataPortalDataset
from cirro.sdk.exceptions import DataPortalAssetNotFound, DataPortalInputError


def expose_param(
    title: str,
    default: Any,
    description=None,
    **kwargs
):
    """
    Set up a variable parameter which can be specified by the user from
    a web form for the purpose of running a notebook non-interactively.

    Inputs:
        title:          Name of the parameter
        default:        Default value of the parameter
        description:    (optional) Description of the parameter
    
    Any additional keyword arguments will be used as parameters of
    the JSON schema which renders the webform.
    """

    # Check the type of the default value
    param_type = _get_param_type(default)

    # Format the ID of the element
    id = _get_id(title)

    # If there is a description
    if description is not None:
        # Then it must be a string
        if not isinstance(description, str):
            raise DataPortalInputError("Description must be a string")

    # Check to see if there is a value provided in .cirro/params.json
    # (which would indicate that this notebook is running in headless mode)
    if _load_param(id, param_type) is not None:
        
        # Use the value from that file
        return _load_param(id, param_type)
    
    # If no value is present, the notebook must be running interactively
    else:

        # Add the parameter definition to the .cirro/form.json
        _save_param_schema(
            title=title,
            id=id,
            type=param_type,
            description=description,
            default=default,
            **kwargs
        )

        # Return the default value
        return default
    

def _save_param_schema(**param_schema):
    """
    Add the parameter schema to .cirro/form.json
    """

    # If the default value is a Dataset
    if isinstance(param_schema['default'], DataPortalDataset):

        # Convert to {project_uuid}::{dataset_uuid}
        param_schema['default'] = _dehydrate_dataset(param_schema['default'])

    # Load the existing schema
    schema = FormSchema()

    # Add the param
    schema.add_param(**param_schema)

    # Save the updated schema
    schema.save()


def _dehydrate_dataset(ds: DataPortalDataset) -> str:
    """Return the {project_uuid}::{dataset_uuid}"""

    return f"{ds.project_id}::{ds.id}"


def _hydrate_dataset(val: str) -> DataPortalDataset:
    """Parse the {project_id}::{dataset_id} to the Dataset object."""

    if not "::" in val:
        raise DataPortalInputError(f"Invalid Dataset id: {val}")
    
    # Parse the project ID and dataset ID
    project_id, dataset_id = val.split("::", 1)

    try:
        portal = DataPortal()
    except Exception as e:
        msg = f"Could not instantiate DataPortal: {str(e)}"
        raise DataPortalAssetNotFound(msg)
    
    try:
        project = portal.get_project_by_id(project_id)
    except Exception as e:
        msg = f"Could not load project {project_id}: {str(e)}"
        raise DataPortalAssetNotFound(msg)

    try:
        dataset = project.get_dataset_by_id(dataset_id)
    except Exception as e:
        msg = f"Could not load dataset {dataset_id}: {str(e)}"
        raise DataPortalAssetNotFound(msg)
    
    return dataset
    

class FormSchema:
    """Form schema object"""

    def __init__(self, fp=".cirro/form.json"):
        self._fp = fp

        if Path(fp).exists():
            self._schema = self._load_schema()
        else:
            self._schema = self._empty_schema()

    def add_param(self, **param_schema):
        """Add a param to the schema."""

        # If the parameter already exists
        saved_param = self._schema['form']['properties'].get(id)
        if saved_param is not None:

            # If any of the values are different
            for kw, new_val in param_schema.items():
                old_val = saved_param.get(kw)
                # Warn the user
                if old_val != new_val:
                    print(f"Warning - changing {kw} of '{id}' from {old_val} to {new_val}")

        # Set up the parameter definition
        self._schema['form']['properties'][id] = param_schema

    def save(self):
        """Save the schema as JSON."""
        with open(self._fp, 'w') as handle:
            json.dump(self._schema, handle, indent=4)

    def _load_schema(self) -> dict:
        with open(self._fp, 'r') as handle:
            schema: dict = json.load(handle)

        if not isinstance(schema, dict):
            msg = f"Invalid schema: {self._fp} - requires dict"
            raise DataPortalAssetNotFound(msg)

        for kw in ['form', 'ui']:
            if schema.get(kw) is None:
                msg = f"Invalid schema: {self._fp} - missing {kw}"
                raise DataPortalAssetNotFound(msg)

            if not isinstance(schema[kw], dict):
                msg = f"Invalid schema: {self._fp} - {kw} should be dict"
                raise DataPortalAssetNotFound(msg)
            
        return schema

    def _empty_schema(self) -> dict:
        return dict(
            form=dict(
                type='object',
                properties=dict()
            ),
            ui=dict()
        )


@lru_cache
def _load_param(id: str, param_type: str):
    """Check to see if there is a value provided in .cirro/params.json."""

    if Path('.cirro').exists() and Path('.cirro/params.json').exists():
        with open('.cirro/params.json', 'r') as handle:
            params = json.load(handle)
            val = params.get(id)

            # If the value is expected to be a dataset
            if param_type == "dataset":
                return _hydrate_dataset(val)
            # For all other values
            else:
                return val


def _get_id(title: str):
    """Format the ID of the element"""

    # The title must be a string
    if not isinstance(title, str):
        raise DataPortalInputError("Parameter title must be a string")

    # The title may only contain letters, numbers, space, underscore, and dash
    if not re.match("^[A-Za-z0-9_- ]*$", title):
        msg = "Parameter title may only contain numbers, letters, and minimal punctuation"
        raise DataPortalInputError(msg)
    
    # The first character must be a letter
    if not re.match("^[A-Za-z]$", title[:1]):
        msg = "The first character must be a letter"
        raise DataPortalInputError(msg)
    
    id = title.lower()
    for chr in [' ', '-']:
        id = id.replace(chr, '_')

    return id


def _get_param_type(default):
    """Map the type of the default value to the form schema."""

    param_type = {
        bool: "boolean",
        str: "string",
        int: "integer",
        float: "number",
        DataPortalDataset: "dataset"
    }.get(type(default))

    if param_type is None:
        msg = f"Default value must be bool, str, int, or float (not {type(default)})"
        raise DataPortalInputError(msg)

    return param_type
