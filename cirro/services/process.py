from functools import cache
from pathlib import Path
from typing import List

from cirro_api_client.v1.api.processes import get_processes, get_process, get_process_parameters, \
    validate_file_requirements
from cirro_api_client.v1.models import ValidateFileRequirementsRequest

from cirro.models.form_specification import ParameterSpecification
from cirro.services.base import BaseService


class ProcessService(BaseService):
    def list(self):
        """
        Retrieves a list of available processes
        """
        return get_processes.sync(client=self._api_client)

    def get(self, process_id: str):
        """
        Retrieves detailed information on a process
        """
        return get_process.sync(process_id=process_id, client=self._api_client)

    def find_by_name(self, name: str):
        """
        Get a process by its display name
        """
        matched_process = next((p for p in self.list() if p.name == name), None)
        if not matched_process:
            return None

        return self.get(matched_process.id)

    @cache
    def get_parameter_spec(self, process_id: str) -> ParameterSpecification:
        """
        Gets a specification used to describe the parameters used in the process
        """
        form_spec = get_process_parameters.sync(process_id=process_id, client=self._api_client)
        return ParameterSpecification(form_spec)

    def check_dataset_files(self, files: List[str], process_id: str, directory: str):
        """
        Checks if the file mapping rules for a process are met by the list of files
        :param files: file names to check
        :param process_id: ID for the process containing the file mapping rules
        :param directory: path to directory containing files
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

        # These will be errors for missing files
        all_errors = [
            entry.error_msg for entry in requirements.allowed_data_types
            if entry.error_msg is not None
        ]
        patterns = [' or '.join([e.example_name for e in entry.allowed_patterns])
                    for entry in requirements.allowed_data_types]

        if len(all_errors) != 0:
            raise ValueError("Files do not meet dataset type requirements. The expected files are: \n" +
                             "\n".join(patterns))
