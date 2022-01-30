from typing import Optional

import boto3

from pubweb.auth import Creds
from pubweb.dataset.models import DatasetInput, DatasetCreateResponse
from pubweb.file_utils import upload_directory
from pubweb.rest_client import RestClient


class Dataset:
    def __init__(self, dataset_input: DatasetInput, rest_client: RestClient):
        self.client = rest_client
        self.data = dataset_input
        self.dataset_id: Optional[str] = None
        self.upload_credentials: Optional[Creds] = None

    def create(self):
        print(f"Creating dataset {self.data['name']}")
        create_response = self.client.post('dataset', self.data)
        create_response.raise_for_status()
        data: DatasetCreateResponse = create_response.json()

        self.dataset_id = data['datasetId']
        self.upload_credentials = data['credentials']

    def upload_directory(self, directory):
        path = f'datasets/{self.dataset_id}/data'
        bucket = f'z-{self.data["project"]}'
        s3_client = boto3.client('s3',
                                 aws_access_key_id=self.upload_credentials['AccessKeyId'],
                                 aws_secret_access_key=self.upload_credentials['SecretAccessKey'],
                                 aws_session_token=self.upload_credentials['SessionToken'])

        upload_directory(directory, s3_client, bucket, path)
