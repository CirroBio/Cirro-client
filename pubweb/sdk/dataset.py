from typing import Union
from pubweb.api.clients.portal import DataPortalClient
from pubweb.api.models.dataset import Dataset
from pubweb.api.models.process import RunAnalysisCommand
from pubweb.sdk.asset import DataPortalAssets
from pubweb.sdk.exceptions import DataPortalAssetNotFound, DataPortalInputError
from pubweb.sdk.file import DataPortalFile, DataPortalFiles
from pubweb.sdk.portal import DataPortal
from pubweb.sdk.process import DataPortalProcess


class DataPortalDataset:
    """
    Datasets in the Data Portal are collections of files which have
    either been uploaded directly, or which have been output by
    an analysis pipeline or notebook.
    """

    def __init__(self, dataset: Dataset, client: DataPortalClient):
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
        params={},
        notifications_emails=[]
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

        # If the process is a string, try to parse it as a process name or ID
        if isinstance(process, str):

            # Make a Portal object
            portal = DataPortal(self._client)

            # Try to parse it as a name
            try:
                process = portal.get_process_by_name(process)
            except DataPortalAssetNotFound:
                pass

            # If that didn't work
            if isinstance(process, str):

                # Try to parse it as an ID
                try:
                    process = portal.get_process_by_id(process)
                except DataPortalAssetNotFound:

                    # Raise an error indicating that the process couldn't be parsed
                    raise DataPortalInputError(f"Could not parse process name or id: '{process}'")

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


class DataPortalDatasets(DataPortalAssets):
    asset_name = "dataset"
    asset_class = DataPortalDataset
