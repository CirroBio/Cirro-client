from typing import Union

from cirro_api_client.v1.errors import UnexpectedStatus
from cirro_api_client.v1.models import ProcessDetail

from cirro.cirro_client import Cirro

from cirro.sdk.exceptions import DataPortalInputError
from cirro.sdk.process import DataPortalProcess


def parse_process_name_or_id(process: Union[DataPortalProcess, str], client: Cirro):
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
        process = client.processes.get(process)
        if isinstance(process, ProcessDetail):
            return DataPortalProcess(process, client)

    # Catch the error if no process is found
    except UnexpectedStatus:
        pass

    # If that didn't work, try to parse it as a name
    try:
        process = client.processes.find_by_name(process) or process
        if isinstance(process, ProcessDetail):
            return DataPortalProcess(process, client)

    # Catch the error if no process is found
    except UnexpectedStatus:
        pass

    # If that didn't work, raise an error indicating that the process couldn't be parsed
    raise DataPortalInputError(f"Could not parse process name or id: '{process}'")
