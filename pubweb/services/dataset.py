import json
from typing import List

from gql import gql

from pubweb.clients import S3Client
from pubweb.clients.utils import filter_deleted, GET_FILE_ACCESS_TOKEN_QUERY
from pubweb.file_utils import upload_directory, download_directory
from pubweb.models.auth import Creds
from pubweb.models.dataset import CreateIngestDatasetInput, DatasetCreateResponse
from pubweb.services.base import BaseService
from pubweb.services.project import get_bucket


def _get_dataset_files(dataset_id: str, project_id: str, s3_client: S3Client) -> List[str]:
    manifest_path = f'datasets/{dataset_id}/web/manifest.json'
    file = s3_client.get_file(bucket=get_bucket(project_id), key=manifest_path)
    manifest = json.loads(file)
    return [file['file'] for file in manifest['files']]


class DatasetService(BaseService):
    def find_by_project(self, project_id):
        query = gql('''
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
        ''')
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
        print(f"Creating dataset {create_request['name']}")
        query = gql('''
          mutation CreateIngestDataset($input: CreateIngestDatasetInput!) {
            createIngestDataset(input: $input) {
              datasetId
              dataPath
            }
          }
        ''')
        variables = {'input': create_request}
        data: DatasetCreateResponse = self._api_client.query(query, variables=variables)['createIngestDataset']
        print(f"Dataset ID: {data['datasetId']}")
        return data

    def upload_files(self, project_id: str, dataset_id: str, directory: str, files: List[str]):
        if not dataset_id:
            raise RuntimeError('Dataset has not been created')
        token_request = {
            'projectId': project_id,
            'datasetId': dataset_id,
            'accessType': 'DATASET',
            'operation': 'UPLOAD'
        }
        variables = {'input': token_request}
        credentials_response = self._api_client.query(GET_FILE_ACCESS_TOKEN_QUERY,
                                                      variables=variables)
        credentials: Creds = credentials_response['getFileAccessToken']

        s3_client = S3Client(credentials)

        path = f'datasets/{dataset_id}/data'
        upload_directory(directory, files, s3_client, get_bucket(project_id), path)

    def download_files(self, project_id: str, dataset_id: str, download_location: str):
        token_request = {
            'projectId': project_id,
            'datasetId': dataset_id,
            'accessType': 'PROJECT',
            'operation': 'DOWNLOAD'
        }
        variables = {'input': token_request}
        credentials_response = self._api_client.query(GET_FILE_ACCESS_TOKEN_QUERY,
                                                      variables=variables)
        credentials: Creds = credentials_response['getFileAccessToken']

        s3_client = S3Client(credentials)

        prefix = f'datasets/{dataset_id}'
        files = _get_dataset_files(dataset_id, project_id, s3_client)
        download_directory(download_location, s3_client, get_bucket(project_id), prefix, files)
