from cirro_api_client.v1.api.datasets import get_sample_sheets
from cirro_api_client.v1.api.processes import validate_file_name_patterns
from cirro_api_client.v1.models import SampleSheets, ValidateFileNamePatternsRequest, FileNameMatch

from cirro import CirroApi


class DeveloperHelper:
    """
    Helper class for developer-related tasks,
    such as adding samplesheet preprocessing for a pipeline
    or testing file name validation and sample autopopulation.
    """

    def __init__(self, client: CirroApi):
        self.client = client

    def generate_samplesheets_for_dataset(self, project_id: str, dataset_id: str) -> SampleSheets:
        """
        Generates Cirro samplesheets for a given dataset
        """
        return get_sample_sheets.sync(
            project_id=project_id,
            dataset_id=dataset_id,
            client=self.client.api_client
        )

    def generate_samplesheets_for_datasets(self, project_id: str, dataset_ids: list[str]) -> SampleSheets:
        """
        Generates Cirro samplesheets for multiple datasets in a project.
        """
        import pandas
        samplesheets_dfs = []
        files_dfs = []
        for dataset_id in dataset_ids:
            samplesheet = self.generate_samplesheets_for_dataset(project_id, dataset_id)
            samplesheets_dfs.append(pandas.read_csv(samplesheet.samples))
            files_dfs.append(pandas.read_csv(samplesheet.files))

        samplesheets_df = pandas.concat(samplesheets_dfs, ignore_index=True)
        files_df = pandas.concat(files_dfs, ignore_index=True)
        return SampleSheets(
            samples=samplesheets_df.to_csv(index=False),
            files=files_df.to_csv(index=False)
        )

    def test_file_name_validation_for_dataset(self, project_id: str, dataset_id: str, file_name_patterns: list[str]) -> list[FileNameMatch]:
        """
        Tests the file name validation for a given dataset against specified regex patterns.

        Used when configuring Cirro's sample autopopulation feature.
        More info: https://docs.cirro.bio/features/samples/#using-auto-population
        """
        dataset_files = self.client.datasets.get_assets_listing(project_id=project_id, dataset_id=dataset_id).files
        file_names = [file.relative_path for file in dataset_files]
        return self.test_file_name_validation(file_names, file_name_patterns)


    def test_file_name_validation(self, file_names: list[str], file_name_patterns: list[str]):
        """
        Tests the file name validation for a list of file names against specified regex patterns.
        """
        request_body = ValidateFileNamePatternsRequest(
            file_names=file_names,
            file_name_patterns=file_name_patterns
        )

        matches = validate_file_name_patterns.sync(
            process_id="test",
            body=request_body,
            client=self.client.api_client
        )
        return matches
