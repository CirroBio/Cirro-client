from typing import Union, List, Optional

from cirro_api_client.v1.models import Dataset, DatasetDetail, RunAnalysisRequest, FileEntry, RunAnalysisRequestParams

from cirro.cirro_client import Cirro
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

    def __init__(self, dataset: Union[Dataset, DatasetDetail], client: Cirro):
        assert dataset.project_id is not None, "Must provide dataset with project_id attribute"
        self.data = dataset
        self._files: Optional[List[FileEntry]] = None
        self._client = client

    @property
    def id(self):
        return self.data.id

    @property
    def name(self):
        return self.data.name

    @property
    def description(self):
        return self.data.description

    @property
    def process_id(self):
        return self.data.process_id

    @property
    def process(self):
        return self._client.processes.get(self.process_id)

    @property
    def project_id(self):
        return self.data.project_id

    @property
    def status(self):
        return self.data.status

    @property
    def source_dataset_ids(self):
        return self.data.source_dataset_ids

    @property
    def source_datasets(self):
        return [
            DataPortalDataset(
                dataset=self._client.datasets.get(project_id=self.project_id, dataset_id=dataset_id),
                client=self._client
            )
            for dataset_id in self.source_dataset_ids
        ]

    @property
    def params(self):
        return self._get_detail().params

    @property
    def info(self):
        return self._get_detail().info

    @property
    def tags(self):
        return self.data.tags

    @property
    def created_by(self):
        return self.data.created_by

    @property
    def created_at(self):
        return self.data.created_at

    def _get_detail(self):
        if not isinstance(self.data, DatasetDetail):
            self.data = self._client.datasets.get(project_id=self.project_id, dataset_id=self.id)
        return self.data

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description', 'status']
        ])

    def list_files(self) -> DataPortalFiles:
        """Return the list of files which make up the dataset."""
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
        """Download all the files from the dataset to a local directory."""

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

        return self._client.execution.run_analysis(
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


class DataPortalDatasets(DataPortalAssets[DataPortalDataset]):
    """Collection of multiple DataPortalDataset objects."""
    asset_name = "dataset"
