import logging
from typing import List, Union

from cirro_api_client.v1.api.datasets import get_datasets, get_dataset, import_public_dataset, upload_dataset, \
    update_dataset, delete_dataset, get_dataset_manifest
from cirro_api_client.v1.models import ImportDataRequest, UploadDatasetRequest, UpdateDatasetRequest, Dataset

from cirro.models.file import FileAccessContext, File
from cirro.services.base import get_all_records
from cirro.services.file import FileEnabledService

logger = logging.getLogger()


class DatasetService(FileEnabledService):
    def list(self, project_id: str, max_items: int = 10000) -> List[Dataset]:
        """List datasets

         Retrieves a list of datasets for a given project

        Args:
            project_id (str): ID of the Project
            max_items (int): Maximum number of records to get (default 10,000)
        """
        return get_all_records(
            records_getter=lambda page_args: get_datasets.sync(project_id=project_id,
                                                               client=self._api_client,
                                                               next_token=page_args.next_token,
                                                               limit=page_args.limit),
            max_items=max_items
        )

    def import_public(self, project_id: str, import_request: ImportDataRequest):
        """
        Download data from public repositories
        """
        return import_public_dataset.sync(project_id=project_id, client=self._api_client, body=import_request)

    def create(self, project_id: str, upload_request: UploadDatasetRequest):
        """
        Registers a dataset in the system that you upload files into
        """
        return upload_dataset.sync(project_id=project_id, client=self._api_client, body=upload_request)

    def get(self, project_id: str, dataset_id: str):
        """
        Gets detailed information about a dataset
        """
        return get_dataset.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def update(self, project_id: str, dataset_id: str, request: UpdateDatasetRequest):
        """
        Update info on a dataset
        """
        return update_dataset.sync(project_id=project_id, dataset_id=dataset_id, body=request, client=self._api_client)

    def delete(self, project_id: str, dataset_id: str):
        """
        Deletes the dataset, files are saved according to the project's retention time.
        """
        delete_dataset.sync_detailed(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def get_file_listing(self, project_id: str, dataset_id: str):
        """
        Gets a listing of files, charts, and other assets available for the dataset
        """
        manifest = get_dataset_manifest.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)
        files = [
            File.from_file_entry(f, project_id=project_id, domain=manifest.domain)
            for f in manifest.files
        ]
        return files

    def upload_files(self, project_id: str, dataset_id: str, local_directory: str, files: List[str]):
        """
        Uploads files to a given dataset from the specified local directory
        """
        dataset = self.get(project_id, dataset_id)
        access_context = FileAccessContext.upload_dataset(project_id=project_id,
                                                          dataset_id=dataset_id,
                                                          base_url=dataset.s3)
        self._file_service.upload_files(access_context, local_directory, files)

    def download_files(self, project_id: str, dataset_id: str, download_location: str,
                       files: Union[List[File], List[str]] = None):
        """
         Downloads all the dataset files
         If the files argument isn't provided, all files will be downloaded
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
