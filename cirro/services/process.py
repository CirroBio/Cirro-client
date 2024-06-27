from pathlib import Path
from typing import List, Optional

from cirro_api_client.v1.api.processes import get_processes, get_process, get_process_parameters, \
    validate_file_requirements, archive_custom_process
from cirro_api_client.v1.models import ValidateFileRequirementsRequest, Executor, Process, ProcessDetail

from cirro.models.form_specification import ParameterSpecification
from cirro.services.base import BaseService


class ProcessService(BaseService):
    """
    Service for interacting with the Process endpoints
    """
    def list(self, process_type: Executor = None) -> List[Process]:
        """
        Retrieves a list of available processes

        Args:
            process_type (`cirro_api_client.v1.models.Executor`): Optional process type (INGEST, CROMWELL, or NEXTFLOW)
        """
        processes = get_processes.sync(client=self._api_client)
        return [p for p in processes if not process_type or process_type == p.executor]

    def get(self, process_id: str) -> ProcessDetail:
        """
        Retrieves detailed information on a process

        Args:
            process_id (str): Process ID
        """
        return get_process.sync(process_id=process_id, client=self._api_client)

    def archive(self, process_id: str):
        """
        Removes a custom process from the list of available processes.

        Error will be raised if the requested process does not exist. No value
        is returned, and no error raised if process exists and request is satisfied.

        Args:
            process_id (str): Process ID
        """
        archive_custom_process.sync_detailed(process_id=process_id, client=self._api_client)

    def find_by_name(self, name: str) -> Optional[ProcessDetail]:
        """
        Get a process by its display name

        Args:
            name (str): Process name
        """
        matched_process = next((p for p in self.list() if p.name == name), None)
        if not matched_process:
            return None

        return self.get(matched_process.id)

    def get_parameter_spec(self, process_id: str) -> ParameterSpecification:
        """
        Gets a specification used to describe the parameters used in the process

        Args:
            process_id (str): Process ID
        """
        form_spec = get_process_parameters.sync(process_id=process_id, client=self._api_client)
        return ParameterSpecification(form_spec)

    def check_dataset_files(self, files: List[str], process_id: str, directory: str):
        """
        Checks if the file mapping rules for a process are met by the list of files

        Error will be raised if the file mapping rules for the process are not met.
        No value is returned and no error is raised if the rules are satisfied.

        Args:
            process_id (str): ID for the process containing the file mapping rules
            directory: path to directory containing files
            files (List[str]): File names to check
        """
        # Parse sample sheet file if present
        sample_sheet = None
        sample_sheet_file = Path(directory, 'samplesheet.csv')
        if sample_sheet_file.exists():
            sample_sheet = sample_sheet_file.read_text()

        request = ValidateFileRequirementsRequest(
            file_names=files,
            sample_sheet=sample_sheet
        )
        requirements = validate_file_requirements.sync(process_id=process_id, body=request, client=self._api_client)

        # These will be sample sheet errors or no files errors
        if error_msg := requirements.error_msg:
            raise ValueError(error_msg)

        errors = [
            f'{entry.description}. {entry.error_msg}. We accept any of the following naming conventions: \n\t- ' +
            '\n\t- '.join([
                e.example_name
                for e in entry.allowed_patterns
            ])
            for entry in requirements.allowed_data_types
            if entry.error_msg is not None
        ]

        files_provided = ', '.join(files)

        if len(errors) != 0:
            raise ValueError(f"The files you have provided are: {files_provided} \n\n"
                             "They do not meet the dataset requirements. "
                             "The required file types are: \n" +
                             "\n".join(errors))
