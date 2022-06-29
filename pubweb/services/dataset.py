import json
from typing import List

from pubweb.clients.utils import filter_deleted
from pubweb.models.dataset import CreateIngestDatasetInput, DatasetCreateResponse
from pubweb.models.file import FileAccessContext
from pubweb.services.file import FileEnabledService


class DatasetService(FileEnabledService):
    def find_by_project(self, project_id: str):
        """ Lists datasets by project """
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
        resp = self._api_client.query(query, variables=variables)['datasetsByProject']
        return filter_deleted(resp['items'])

    def create(self, create_request: CreateIngestDatasetInput) -> DatasetCreateResponse:
        """
        Creates an ingest dataset
        """
        print(f"Creating dataset {create_request['name']}")
        query = '''
          mutation CreateIngestDataset($input: CreateIngestDatasetInput!) {
            createIngestDataset(input: $input) {
              datasetId
              dataPath
            }
          }
        '''
        variables = {'input': create_request}
        data: DatasetCreateResponse = self._api_client.query(query, variables=variables)['createIngestDataset']
        print(f"Dataset ID: {data['datasetId']}")
        return data

    def get_dataset_files(self, project_id: str, dataset_id: str) -> List[str]:
        """
        Returns a list of file names that are in the provided dataset
        """
        access_context = FileAccessContext.download_dataset(project_id=project_id, dataset_id=dataset_id)
        return self._get_dataset_files(access_context)

    def upload_files(self, project_id: str, dataset_id: str, directory: str, files: List[str]):
        access_context = FileAccessContext.upload_dataset(project_id=project_id, dataset_id=dataset_id)
        self._file_service.upload_files(access_context, directory, files)

    def download_files(self, project_id: str, dataset_id: str, download_location: str, files: List[str] = None):
        """
         Downloads all the dataset files
         If the files argument isn't provided, all files will be downloaded
        """
        access_context = FileAccessContext.download_dataset(project_id=project_id, dataset_id=dataset_id)
        if files is None:
            files = self._get_dataset_files(access_context)
        self._file_service.download_files(access_context, download_location, files)

    def _get_dataset_files(self, access_context: FileAccessContext):
        file = self._file_service.get_file(access_context, 'web/manifest.json')
        manifest = json.loads(file)
        return [file['file'] for file in manifest['files']]
