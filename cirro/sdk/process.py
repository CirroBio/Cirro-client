from typing import List

from cirro_api_client.v1.models import Process, Executor

from cirro.cirro_client import Cirro
from cirro.models.form_specification import ParameterSpecification
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset


class DataPortalProcess(DataPortalAsset):
    """Helper functions for interacting with analysis processes."""
    data: Process

    def __init__(self, process: Process, client: Cirro):
        self.data = process
        self._client = client

    @property
    def id(self) -> str:
        return self.data.id

    @property
    def name(self) -> str:
        return self.data.name

    @property
    def description(self) -> str:
        return self.data.description

    @property
    def child_process_ids(self) -> List[str]:
        return self.data.child_process_ids

    @property
    def executor(self) -> Executor:
        return self.data.executor

    @property
    def documentation_url(self) -> str:
        return self.data.documentation_url

    @property
    def file_requirements_message(self) -> str:
        return self.data.file_requirements_message

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
