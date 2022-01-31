import json
from typing import Optional, List

import boto3

from pubweb.clients.auth import Creds
from pubweb.dataset.models import DatasetCreateResponse, CreateDatasetRequest
from pubweb.file_utils import upload_directory, download_directory
from pubweb.clients.rest import RestClient


def get_s3_client(credentials: Creds):
    return boto3.client('s3',
                        aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken'])


class Dataset:
    def __init__(self, rest_client: RestClient, dataset=None):
        if dataset is None:
            dataset = {}
        self.client = rest_client
        self.dataset_id: Optional[str] = dataset.get('dataset')
        self.project_id: Optional[str] = dataset.get('project')
        self.upload_credentials: Optional[Creds] = None

    def create(self, dataset_input: CreateDatasetRequest):
        print(f"Creating dataset {dataset_input['name']}")
        create_response = self.client.post('dataset', dataset_input)
        create_response.raise_for_status()
        data: DatasetCreateResponse = create_response.json()

        self.project_id = dataset_input['project']
        self.dataset_id = data['datasetId']
        self.upload_credentials = data['credentials']

    def upload_directory(self, directory):
        if not self.dataset_id:
            raise RuntimeError('Dataset has not been created')
        path = f'datasets/{self.dataset_id}/data'
        s3_client = get_s3_client(self.upload_credentials)

        upload_directory(directory, s3_client, self._get_bucket(), path)

    def download_files(self, directory):
        credentials_response = self.client.get('project/fileAccessToken', {'projectId': self.project_id})
        credentials_response.raise_for_status()
        credentials: Creds = credentials_response.json()
        s3_client = get_s3_client(credentials)
        prefix = f'datasets/{self.dataset_id}/'
        files = self._get_dataset_files(s3_client)
        download_directory(directory, s3_client, self._get_bucket(), prefix, files)

    def _get_dataset_files(self, s3_client) -> List[str]:
        manifest_path = f'datasets/{self.dataset_id}/web/manifest.json'
        file = s3_client.get_object(Bucket=self._get_bucket(),
                                    Key=manifest_path)['Body']
        info = json.loads(file.read().decode('utf-8'))
        return [file['file'] for file in info['files']]

    def _get_bucket(self):
        return f'z-{self.project_id}'

