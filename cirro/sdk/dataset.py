from functools import lru_cache
from typing import Union

from cirro.api.clients.portal import DataPortalClient
from cirro.api.models.dataset import Dataset
from cirro.api.models.exceptions import DataPortalModelException
from cirro.api.models.process import RunAnalysisCommand
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset
from cirro.exceptions import DataPortalInputError
from cirro.sdk.file import DataPortalFile, DataPortalFiles
from cirro.sdk.helpers import parse_process_name_or_id
from cirro.sdk.process import DataPortalProcess


class DataPortalDataset(DataPortalAsset):
    """
    Datasets in the Data Portal are collections of files which have
    either been uploaded directly, or which have been output by
    an analysis pipeline or notebook.
    """
    name = None

    def __init__(self, dataset: Dataset, client: DataPortalClient):
        assert dataset.project_id is not None, "Must provide dataset with project_id attribute"
        self.id = dataset.id
        self.name = dataset.name
        self.description = dataset.description
        self.process_id = dataset.process_id
        self.project_id = dataset.project_id
        self.status = dataset.status
        self.source_dataset_ids = dataset.source_dataset_ids
        self.info = dataset.info
        self.params = dataset.params
        self.created_at = dataset.created_at
        self._client = client

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description', 'status']
        ])

    @lru_cache
    def list_files(self) -> DataPortalFiles:
        """Return the list of files which make up the dataset."""

        return DataPortalFiles(
            [
                DataPortalFile(
                    f,
                    client=self._client
                )
                for f in self._client.dataset.get_dataset_files(
                    project_id=self.project_id,
                    dataset_id=self.id
                )
            ]
        )

    def get_file(self, name):
        """
        Return the indicated file in the dataset.
        Query by:
            1. Exact match of file path
            2. Exact match of file name
            3. Wildcard expression
        """

        # Get the full list of files
        files = self.list_files()

        # Check for an exact match of the full filepath
        matching = [f for f in files if f.name == name]
        # If there is only one
        if len(matching) == 1:
            # Return the match
            return matching[0]

        # Check for an exact match of the file name
        matching = [f for f in files if f.name.rsplit("/")[-1] == name]
        # If there is only one
        if len(matching) == 1:
            # Return the match
            return matching[0]

        # Filter on wildcard glob
        matching = files.filter_by_pattern(name)
        # If there is only one
        if len(matching) == 1:
            # Return the match
            return matching[0]

        # Otherwise, inform the user and return None
        print(f"Could not find a file uniquely matching {name}")

    def download_files(self, download_location: str = None) -> None:
        """Download all of the files from the dataset to a local directory."""

        # Alias for internal method
        self.list_files().download(download_location)

    def run_analysis(
            self,
            name: str = None,
            description: str = "",
            process: Union[DataPortalProcess, str] = None,
            params=None,
            notifications_emails=None
    ) -> str:
        """
        Runs an analysis on a dataset, returns the ID of the new dataset.
        The process can be provided as either a DataPortalProcess object,
        or a string which corresponds to the name or ID of the process.
        """
        if self._in_headless:
            raise DataPortalModelException("Cannot run analysis in headless mode")
        if name is None:
            raise DataPortalInputError("Must specify 'name' for run_analysis")
        if process is None:
            raise DataPortalInputError("Must specify 'process' for run_analysis")
        if notifications_emails is None:
            notifications_emails = []
        if params is None:
            params = {}

        # If the process is a string, try to parse it as a process name or ID
        process = parse_process_name_or_id(process, self._client)

        return self._client.process.run_analysis(
            RunAnalysisCommand(
                name=name,
                description=description,
                process_id=process.id,
                parent_dataset_id=self.id,
                project_id=self.project_id,
                params=params,
                notifications_emails=notifications_emails
            )
        )


class DataPortalDatasets(DataPortalAssets[DataPortalDataset]):
    """Collection of multiple DataPortalDataset objects."""
    asset_name = "dataset"
