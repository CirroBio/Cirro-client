import datetime
from typing import Union, List, Optional

from cirro_api_client.v1.models import Dataset, DatasetDetail, RunAnalysisRequest, FileEntry, \
    ProcessDetail, Status, DatasetDetailParams, RunAnalysisRequestParams, DatasetDetailInfo, \
    Tag

from cirro.cirro_client import CirroApi
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset
from cirro.sdk.exceptions import DataPortalInputError
from cirro.sdk.file import DataPortalFile, DataPortalFiles
from cirro.sdk.helpers import parse_process_name_or_id
from cirro.sdk.process import DataPortalProcess


class DataPortalDataset(DataPortalAsset):
    """
    Datasets in the Data Portal are collections of files which have
    either been uploaded directly, or which have been output by
    an analysis pipeline or notebook.
    """

    def __init__(self, dataset: Union[Dataset, DatasetDetail], client: CirroApi):
        """
        Instantiate a dataset object

        Should be invoked from a top-level constructor, for example:

        ```python
        from cirro import DataPortal()
        portal = DataPortal()
        dataset = portal.get_dataset(
            project="id-or-name-of-project",
            dataset="id-or-name-of-dataset"
        )
        ```

        """
        assert dataset.project_id is not None, "Must provide dataset with project_id attribute"
        self._data = dataset
        self._files: Optional[List[FileEntry]] = None
        self._client = client

    @property
    def id(self) -> str:
        """Unique identifier for the dataset"""
        return self._data.id

    @property
    def name(self) -> str:
        """Editible name for the dataset"""
        return self._data.name

    @property
    def description(self) -> str:
        """Longer name for the dataset"""
        return self._data.description

    @property
    def process_id(self) -> str:
        """Unique ID of process used to create the dataset"""
        return self._data.process_id

    @property
    def process(self) -> ProcessDetail:
        """
        Object representing the process used to create the dataset
        """
        return self._client.processes.get(self.process_id)

    @property
    def project_id(self) -> str:
        """ID of the project containing the dataset"""
        return self._data.project_id

    @property
    def status(self) -> Status:
        """
        Status of the dataset
        """
        return self._data.status

    @property
    def source_dataset_ids(self) -> List[str]:
        """IDs of the datasets used as sources for this dataset (if any)"""
        return self._data.source_dataset_ids

    @property
    def source_datasets(self) -> List['DataPortalDataset']:
        """
        Objects representing the datasets used as sources for this dataset (if any)
        """
        return [
            DataPortalDataset(
                dataset=self._client.datasets.get(project_id=self.project_id, dataset_id=dataset_id),
                client=self._client
            )
            for dataset_id in self.source_dataset_ids
        ]

    @property
    def params(self) -> DatasetDetailParams:
        """
        Parameters used to generate the dataset
        """
        return self._get_detail().params

    @property
    def info(self) -> DatasetDetailInfo:
        """
        Detailed information about the dataset
        """
        return self._get_detail().info

    @property
    def tags(self) -> List[Tag]:
        """
        Tags applied to the dataset
        """
        return self._data.tags

    @property
    def created_by(self) -> str:
        """User who created the dataset"""
        return self._data.created_by

    @property
    def created_at(self) -> datetime.datetime:
        """Timestamp of dataset creation"""
        return self._data.created_at

    def _get_detail(self):
        if not isinstance(self._data, DatasetDetail):
            self._data = self._client.datasets.get(project_id=self.project_id, dataset_id=self.id)
        return self._data

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description', 'status']
        ])

    def list_files(self) -> DataPortalFiles:
        """
        Return the list of files which make up the dataset.
        """
        if not self._files:
            self._files = DataPortalFiles(
                [
                    DataPortalFile(file=file, client=self._client)
                    for file in self._client.datasets.get_file_listing(
                        project_id=self.project_id,
                        dataset_id=self.id
                    )
                ]
            )
        return self._files

    def download_files(self, download_location: str = None) -> None:
        """
        Download all the files from the dataset to a local directory.

        Args:
            download_location (str): Path to local directory
        """

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
        Runs an analysis on a dataset, returns the ID of the newly created dataset.

        The process can be provided as either a DataPortalProcess object,
        or a string which corresponds to the name or ID of the process.

        Args:
            name (str): Name of newly created dataset
            description (str): Description of newly created dataset
            process (DataPortalProcess or str): Process to run
            params (dict): Analysis parameters
            notifications_emails (List[str]): Notification email address(es)

        Returns:
            dataset_id (str): ID of newly created dataset
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

        resp = self._client.execution.run_analysis(
            project_id=self.project_id,
            request=RunAnalysisRequest(
                name=name,
                description=description,
                process_id=process.id,
                source_dataset_ids=[self.id],
                params=RunAnalysisRequestParams.from_dict(params),
                notification_emails=notifications_emails
            )
        )
        return resp.id


class DataPortalDatasets(DataPortalAssets[DataPortalDataset]):
    """Collection of multiple DataPortalDataset objects."""
    asset_name = "dataset"
