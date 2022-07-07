import logging
from typing import List, Union

from pubweb.clients.utils import filter_deleted
from pubweb.models.dataset import CreateIngestDatasetInput, DatasetCreateResponse, Dataset
from pubweb.models.file import FileAccessContext, File
from pubweb.services.base import BaseService
from pubweb.services.file import FileEnabledMixin

logger = logging.getLogger()


class DatasetService(FileEnabledMixin, BaseService):
    def find_by_project(self, project_id: str, name: str = None) -> List[Dataset]:
        """
         Lists datasets by project with an optional name provided
         Dataset names are not unique so providing a name doesn't guarantee one result
        """
        query = '''
          query DatasetsByProject(
            $project: ID!
            $sortDirection: ModelSortDirection
            $filter: ModelDatasetFilterInput
            $limit: Int
            $nextToken: String
          ) {
            datasetsByProject(
              project: $project
              sortDirection: $sortDirection
              filter: $filter
              limit: $limit
              nextToken: $nextToken
            ) {
              items {
                id
                status
                name
                desc
                sourceDatasets
                infoJson
                paramJson
                process
                createdAt
                updatedAt
                _deleted
              }
              nextToken
              startedAt
            }
          }
        '''
        variables = {
            'project': project_id,
            'filter': {
                'status': {
                    'eq': 'COMPLETED'
                }
            }
        }
        if name:
            variables['filter']['name'] = {'eq': name}

        resp = self._api_client.query(query, variables=variables)['datasetsByProject']
        not_deleted = filter_deleted(resp['items'])
        return [Dataset.from_record(item) for item in not_deleted]

    def create(self, create_request: CreateIngestDatasetInput) -> DatasetCreateResponse:
        """
        Creates an ingest dataset
        """
        logger.info(f"Creating dataset {create_request.name}")
        query = '''
          mutation CreateIngestDataset($input: CreateIngestDatasetInput!) {
            createIngestDataset(input: $input) {
              datasetId
              dataPath
            }
          }
        '''
        variables = {'input': create_request.to_json()}
        data: DatasetCreateResponse = self._api_client.query(query, variables=variables)['createIngestDataset']
        logger.info(f"Dataset ID: {data['datasetId']}")
        return data

    def get_dataset_files(self, project_id: str, dataset_id: str) -> List[File]:
        """
        Returns a list of file names that are in the provided dataset
        """
        access_context = FileAccessContext.download_dataset(project_id=project_id, dataset_id=dataset_id)
        return self._file_service.get_file_listing(access_context)

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
        if len(files) == 0:
            return

        if isinstance(files[0], File):
            files = [file.relative_path for file in files]

        access_context = FileAccessContext.download_dataset(project_id=project_id, dataset_id=dataset_id)
        if files is None:
            files = self._file_service.get_file_listing(access_context)

        self._file_service.download_files(access_context, download_location, files)
