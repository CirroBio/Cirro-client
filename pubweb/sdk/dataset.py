from typing import Union

from pubweb.api.clients.portal import DataPortalClient
from pubweb.api.models.dataset import Dataset
from pubweb.api.models.process import RunAnalysisCommand
from pubweb.sdk.asset import DataPortalAssets, DataPortalAsset
from pubweb.sdk.exceptions import DataPortalInputError
from pubweb.sdk.file import DataPortalFile, DataPortalFiles
from pubweb.sdk.helpers import parse_process_name_or_id
from pubweb.sdk.process import DataPortalProcess


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
