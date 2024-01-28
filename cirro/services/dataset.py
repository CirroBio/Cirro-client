import logging
from typing import List, Union

from cirro_api_client.v1.api.datasets import get_datasets, get_dataset, import_public_dataset, upload_dataset, \
    update_dataset, delete_dataset, get_dataset_manifest
from cirro_api_client.v1.models import ImportDataRequest, UploadDatasetRequest, UpdateDatasetRequest

from cirro.models.file import FileAccessContext, File
from cirro.services.base import BaseService
from cirro.services.file import FileEnabledService

logger = logging.getLogger()


class DatasetService(FileEnabledService):
    def list(self, project_id: str):
        """List datasets

         Retrieves a list of datasets for a given project

        Args:
            project_id (str): ID of the Project
        """
        resp = get_datasets.sync(project_id=project_id, client=self._api_client)
        return resp.data

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

    def get_manifest(self, project_id: str, dataset_id: str):
        """
        Gets a listing of files, charts, and other assets available for the dataset
        """
        return get_dataset_manifest.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def upload_files(self, project_id: str, dataset_id: str, directory: str, files: List[str]):
        """
        Uploads files to a given dataset from the specified local directory
        """
        access_context = FileAccessContext.upload_dataset(project_id=project_id, dataset_id=dataset_id)
        self._file_service.upload_files(access_context, directory, files)

    def download_files(self, project_id: str, dataset_id: str, download_location: str,
                       files: Union[List[File], List[str]] = None):
        """
         Downloads all the dataset files
         If the files argument isn't provided, all files will be downloaded
        """
        access_context = FileAccessContext.download_dataset(project_id=project_id, dataset_id=dataset_id)
        manifest = self.get_manifest(project_id, dataset_id)
        if files is None:
            files = manifest.files

        if len(files) == 0:
            return

        if isinstance(files[0], File):
            files = [file.relative_path for file in files]

        self._file_service.download_files(access_context, download_location, files)
