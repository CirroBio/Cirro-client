from pubweb.api.clients.portal import DataPortalClient
from pubweb.api.models.form_specification import ParameterSpecification
from pubweb.api.models.process import Process
from pubweb.sdk.asset import DataPortalAssets, DataPortalAsset


class DataPortalProcess(DataPortalAsset):
    """Helper functions for interacting with analysis processes."""
    name = None

    def __init__(self, process: Process, client: DataPortalClient):

        self.id = process.id
        self.name = process.name
        self.description = process.description
        self.child_process_ids = process.child_process_ids
        self.executor = process.executor
        self.documentation_url = process.documentation_url
        self.code = process.code
        self.form_spec_json = process.form_spec_json
        self.sample_sheet_path = process.sample_sheet_path
        self.file_requirements_message = process.file_requirements_message
        self.file_mapping_rules = process.file_mapping_rules
        self._client = client

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description']
        ])

    def get_parameter_spec(self) -> ParameterSpecification:
        """
        Gets a specification used to describe the parameters used in the process.
        """
        return self._client.process.get_parameter_spec(self.id)


class DataPortalProcesses(DataPortalAssets[DataPortalProcess]):
    """Collection of DataPortalProcess objects."""
    asset_name = "process"
