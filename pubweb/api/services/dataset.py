import json
import logging
import uuid
from typing import List, Union

from pubweb.api.clients.utils import filter_deleted
from pubweb.api.models.dataset import CreateIngestDatasetInput, DatasetCreateResponse, Dataset
from pubweb.api.models.file import FileAccessContext, File
from pubweb.api.services.file import FileEnabledService

logger = logging.getLogger()


class DatasetService(FileEnabledService):
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
                project
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
            },
            # TODO: Implement pagination
            'limit': 10000
        }
        if name:
            variables['filter']['name'] = {'eq': name}

        resp = self._api_client.query(query, variables=variables)['datasetsByProject']
        not_deleted = filter_deleted(resp['items'])
        return [Dataset.from_record(item) for item in not_deleted]

    def create(self, create_request: CreateIngestDatasetInput) -> DatasetCreateResponse:
        """
        Creates an ingest dataset.
        This only registers into the system, does not upload any files
        """
        logger.info(f"Creating dataset {create_request.name}")

        if self._api_client.has_iam_creds:
            return self._write_dataset_manifest(create_request)

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
        access_context = FileAccessContext.download_dataset(project_id=project_id, dataset_id=dataset_id)
        if files is None:
            files = self._file_service.get_file_listing(access_context)

        if len(files) == 0:
            return

        if isinstance(files[0], File):
            files = [file.relative_path for file in files]

        self._file_service.download_files(access_context, download_location, files)

    def _write_dataset_manifest(self, request: CreateIngestDatasetInput) -> DatasetCreateResponse:
        """
         Internal method for registering a dataset without API access.
         To be used for machine or service accounts
        """
        manifest = {
            'project': request.project_id,
            'process': request.process_id,
            'name': request.name,
            'desc': request.description,
            'infoJson': {
                'ingestedBy': self._api_client.current_user
            },
            'files': [{'name': file} for file in request.files]
        }
        dataset_id = str(uuid.uuid4())
        manifest_path = f'datasets/{dataset_id}/artifacts/manifest.json'
        manifest_json = json.dumps(manifest, indent=4)
        access_context = FileAccessContext.upload_dataset(dataset_id=dataset_id,
                                                          project_id=request.project_id)
        self._file_service.create_file(access_context,
                                       key=manifest_path,
                                       contents=manifest_json,
                                       content_type='application/json')
        return {
            'datasetId': dataset_id,
            'dataPath': f'datasets/{dataset_id}/artifacts/data'
        }
