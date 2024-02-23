from typing import List

from cirro_api_client.v1.models import Process, Executor

from cirro.cirro_client import CirroApi
from cirro.models.form_specification import ParameterSpecification
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset


class DataPortalProcess(DataPortalAsset):
    """Helper functions for interacting with analysis processes."""
    _data: Process

    def __init__(self, process: Process, client: CirroApi):
        """
        Instantiate with helper method

        ```python
        from cirro import DataPortal()
        portal = DataPortal()
        process = portal.get_process_by_name("Process Name")
        ```
        """
        self._data = process
        self._client = client

    @property
    def id(self) -> str:
        """Unique identifier"""
        return self._data.id

    @property
    def name(self) -> str:
        """Readable name"""
        return self._data.name

    @property
    def description(self) -> str:
        """Longer description of process"""
        return self._data.description

    @property
    def child_process_ids(self) -> List[str]:
        """List of processes which can be run on the output of this process"""
        return self._data.child_process_ids

    @property
    def executor(self) -> Executor:
        """INGEST, CROMWELL, or NEXTFLOW"""
        return self._data.executor

    @property
    def documentation_url(self) -> str:
        """Documentation URL"""
        return self._data.documentation_url

    @property
    def file_requirements_message(self) -> str:
        """Description of files required for INGEST processes"""
        return self._data.file_requirements_message

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description']
        ])

    def get_parameter_spec(self) -> ParameterSpecification:
        """
        Gets a specification used to describe the parameters used in the process.
        """
        return self._client.processes.get_parameter_spec(self.id)


class DataPortalProcesses(DataPortalAssets[DataPortalProcess]):
    """Collection of DataPortalProcess objects."""
    asset_name = "process"
