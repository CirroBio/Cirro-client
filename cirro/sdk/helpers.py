import json
from pathlib import Path
from typing import Union

from gql.transport.exceptions import TransportQueryError

from cirro.api.clients.portal import DataPortalClient
from cirro.api.models.exceptions import DataPortalModelException
from cirro.api.models.process import Process
from cirro.sdk.exceptions import DataPortalAssetNotFound, DataPortalInputError
from cirro.sdk.process import DataPortalProcess


def parse_process_name_or_id(process: Union[DataPortalProcess, str], client: DataPortalClient):
    """
    If the process is a string, try to parse it as a process name or ID.
    """

    # If the process object is already a DataPortalProcess object
    if isinstance(process, DataPortalProcess):
        return process

    # Otherwise, it should be a string
    if not isinstance(process, str):
        raise DataPortalInputError(f"Process name or ID should be a string: '{process}'")

    # Try to get the process by ID
    try:
        process = client.process.get_process(process)
        if isinstance(process, Process):
            return DataPortalProcess(process, client)

    # Catch the error if no dataset is found
    except (TransportQueryError, DataPortalModelException):
        pass

    # If that didn't work, try to parse it as a name
    try:
        process = client.process.find_by_name(process) or process
        if isinstance(process, Process):
            return DataPortalProcess(process, client)

    # Catch the error if no dataset is found
    except (TransportQueryError, DataPortalModelException):
        pass

    # If that didn't work, raise an error indicating that the process couldn't be parsed
    raise DataPortalInputError(f"Could not parse process name or id: '{process}'")


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
        saved_param = self._schema['form']['properties'].get('id')
        if saved_param is not None:

            # If any of the values are different
            for kw, new_val in param_schema.items():
                old_val = saved_param.get(kw)
                # Warn the user
                if old_val != new_val:
                    msg = f"Warning - changing {kw} of '{saved_param}' from {old_val} to {new_val}"
                    print(msg)

        # Set up the parameter definition
        id = param_schema['id']
        del param_schema['id']
        self._schema['form']['properties'][id] = param_schema

    def save(self):
        """Save the schema as JSON."""
        # If the parent directory doesn't exist
        if not Path(self._fp).parent.exists():
            # Create the parent directory
            Path(self._fp).parent.mkdir(parents=True, exist_ok=True)

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
