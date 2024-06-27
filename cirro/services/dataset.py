from typing import List, Optional, Union

from cirro_api_client.v1.api.datasets import get_datasets, get_dataset, import_public_dataset, upload_dataset, \
    update_dataset, delete_dataset, get_dataset_manifest
from cirro_api_client.v1.models import ImportDataRequest, UploadDatasetRequest, UpdateDatasetRequest, Dataset, \
    DatasetDetail, CreateResponse, UploadDatasetCreateResponse

from cirro.models.file import FileAccessContext, File, PathLike
from cirro.services.base import get_all_records
from cirro.services.file import FileEnabledService


class DatasetService(FileEnabledService):
    """
    Service for interacting with the Dataset endpoints
    """

    def list(self, project_id: str, max_items: int = 10000) -> List[Dataset]:
        """List datasets

        Retrieves a list of datasets for a given project

        Args:
            project_id (str): ID of the Project
            max_items (int): Maximum number of records to get (default 10,000)
        """
        return get_all_records(
            records_getter=lambda page_args: get_datasets.sync(
                project_id=project_id,
                client=self._api_client,
                next_token=page_args.next_token,
                limit=page_args.limit
            ),
            max_items=max_items
        )

    def import_public(self, project_id: str, import_request: ImportDataRequest) -> CreateResponse:
        """
        Download data from public repositories

        Args:
            project_id (str): ID of the Project
            import_request (cirro_api_client.v1.models.ImportDataRequest):

        Returns:
            ID of the created dataset
        """
        return import_public_dataset.sync(project_id=project_id, client=self._api_client, body=import_request)

    def create(self, project_id: str, upload_request: UploadDatasetRequest) -> UploadDatasetCreateResponse:
        """
        Registers a dataset in Cirro, which can subsequently have files uploaded to it

        Args:
            project_id (str): ID of the Project
            upload_request (cirro_api_client.v1.models.UploadDatasetRequest):

        Returns:
            ID of the created dataset and the path to upload files

        ```python
        from cirro_api_client.v1.models import UploadDatasetRequest
        from cirro.cirro_client import CirroApi

        cirro = CirroApi()
        request = UploadDatasetRequest(
            name="Name of new dataset",
            process_id="paired_dnaseq",
            expected_files=["read_1.fastq.gz", "read_2.fastq.gz"],
            description="Description of the dataset"
        )
        cirro.datasets.create("project-id", request)
        ```
        """
        return upload_dataset.sync(project_id=project_id, client=self._api_client, body=upload_request)

    def get(self, project_id: str, dataset_id: str) -> Optional[DatasetDetail]:
        """
        Gets detailed information about a dataset

        Args:
            project_id (str): ID of the Project
            dataset_id (str): ID of the Dataset

        Returns:
            The dataset, if found
        """
        return get_dataset.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def update(self, project_id: str, dataset_id: str, request: UpdateDatasetRequest) -> DatasetDetail:
        """
        Update info on a dataset (name, description, and/or tags)

        Args:
            project_id (str): ID of the Project
            dataset_id (str): ID of the Dataset
            request (cirro_api_client.v1.models.UpdateDatasetRequest):

        Returns:
            The updated dataset

        ```python
        from cirro_api_client.v1.models import UpdateDatasetRequest
        from cirro.cirro_client import CirroApi

        cirro = CirroApi()
        request = UpdateDatasetRequest(
            name="Name of new dataset",
            process_id="paired_dnaseq",
            description="Description of the dataset"
        )
        cirro.datasets.update("project-id", "dataset-id", request)
        ```
        """
        return update_dataset.sync(project_id=project_id, dataset_id=dataset_id, body=request, client=self._api_client)

    def delete(self, project_id: str, dataset_id: str) -> None:
        """
        Delete a dataset

        After a dataset has been deleted, the files associated with that
        dataset are saved according to the project's retention time.

        Args:
            project_id (str): ID of the Project
            dataset_id (str): ID of the Dataset
        """
        delete_dataset.sync_detailed(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def get_file_listing(self, project_id: str, dataset_id: str, file_limit: int = 100000) -> List[File]:
        """
        Gets a listing of files, charts, and other assets available for the dataset

        Args:
            project_id (str): ID of the Project
            dataset_id (str): ID of the Dataset
            file_limit (int): Maximum number of files to get (default 100,000)
        """
        if file_limit < 1:
            raise ValueError("file_limit must be greater than 0")
        all_files = []
        file_offset = 0
        domain = None

        while len(all_files) < file_limit:
            manifest = get_dataset_manifest.sync(
                project_id=project_id,
                dataset_id=dataset_id,
                file_offset=file_offset,
                client=self._api_client
            )
            all_files.extend(manifest.files)
            file_offset += len(manifest.files)

            domain = manifest.domain
            if len(all_files) >= manifest.total_files or len(manifest.files) == 0:
                break

        files = [
            File.from_file_entry(
                f,
                project_id=project_id,
                domain=domain
            )
            for f in all_files
        ]
        return files

    def upload_files(self,
                     project_id: str,
                     dataset_id: str,
                     directory: PathLike,
                     files: List[PathLike]) -> None:
        """
        Uploads files to a given dataset from the specified directory.

        Args:
            project_id (str): ID of the Project
            dataset_id (str): ID of the Dataset
            directory (str|Path): Path to directory
            files (typing.List[str|Path]): List of paths to files within the directory,
                must be the same type as directory.
        """
        dataset = self.get(project_id, dataset_id)

        access_context = FileAccessContext.upload_dataset(
            project_id=project_id,
            dataset_id=dataset_id,
            base_url=dataset.s3
        )

        self._file_service.upload_files(
            access_context=access_context,
            directory=directory,
            files=files
        )

    def download_files(
        self,
        project_id: str,
        dataset_id: str,
        download_location: str,
        files: Union[List[File], List[str]] = None
    ) -> None:
        """
        Downloads files from a dataset

        The `files` argument is used to optionally specify a subset of files
        to be downloaded. By default, all files are downloaded.

        Args:
            project_id (str): ID of the Project
            dataset_id (str): ID of the Dataset
            download_location (str): Local destination for downloaded files
            files (typing.List[str]): Optional list of files to download
        """
        if files is None:
            files = self.get_file_listing(project_id, dataset_id)

        if len(files) == 0:
            return

        first_file = files[0]
        if isinstance(first_file, File):
            files = [file.relative_path for file in files]
            access_context = first_file.access_context
        else:
            dataset = self.get(project_id, dataset_id)
            access_context = FileAccessContext.download(project_id=project_id,
                                                        base_url=dataset.s3)

        self._file_service.download_files(access_context, download_location, files)
