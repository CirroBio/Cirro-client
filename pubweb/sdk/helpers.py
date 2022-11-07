from typing import Union
from pubweb.api.clients.portal import DataPortalClient
from pubweb.api.models.process import Process
from pubweb.api.models.exceptions import DataPortalModelException
from pubweb.sdk.exceptions import DataPortalInputError
from pubweb.sdk.process import DataPortalProcess
from gql.transport.exceptions import TransportQueryError


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
