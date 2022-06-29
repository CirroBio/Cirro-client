import math
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import boto3
from tqdm import tqdm

from pubweb.models.auth import Creds
from pubweb.utils import parse_json_date


def convert_size(size):
    if size == 0:
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size/p, 2)
    return '%.2f %s' % (s, size_name[i])


def build_client(creds: Creds):
    return boto3.client('s3',
                        aws_access_key_id=creds['AccessKeyId'],
                        aws_secret_access_key=creds['SecretAccessKey'],
                        aws_session_token=creds['SessionToken'])


class ProgressPercentage(object):
    def __init__(self, progress: tqdm):
        self._lock = threading.Lock()
        self.progress = progress

    def __call__(self, bytes_amount):
        with self._lock:
            self.progress.update(bytes_amount)


class S3Client:
    def __init__(self, creds_getter: Callable[[], Creds]):
        creds = creds_getter()
        self._creds_getter = creds_getter
        self._creds_expiration = creds['Expiration']
        self._client = build_client(creds)

    def upload_file(self, local_path: Path, bucket: str, key: str):
        self._check_credentials()
        file_size = local_path.stat().st_size
        file_name = local_path.name

        with tqdm(total=file_size,
                  desc=f'Uploading file {file_name} ({convert_size(file_size)})',
                  bar_format="{desc} | {percentage:.1f}%|{bar:25} | {rate_fmt}",
                  unit='B', unit_scale=True,
                  unit_divisor=1024) as progress:
            absolute_path = str(local_path.absolute())
            self._client.upload_file(absolute_path, bucket, key, Callback=ProgressPercentage(progress))

    def download_file(self, local_path: Path, bucket: str, key: str):
        self._check_credentials()
        file_size = self.get_file_stats(bucket, key)['ContentLength']
        file_name = local_path.name

        with tqdm(total=file_size,
                  desc=f'Downloading file {file_name} ({convert_size(file_size)})',
                  bar_format="{desc} | {percentage:.1f}%|{bar:25} | {rate_fmt}",
                  unit='B', unit_scale=True,
                  unit_divisor=1024) as progress:
            absolute_path = str(local_path.absolute())
            self._client.download_file(bucket, key, absolute_path, Callback=ProgressPercentage(progress))

    def get_file(self, bucket: str, key: str) -> str:
        self._check_credentials()
        resp = self._client.get_object(Bucket=bucket, Key=key)
        file_body = resp['Body']
        return file_body.read().decode('utf-8')

    def get_file_stats(self, bucket: str, key: str):
        self._check_credentials()
        return self._client.head_object(Bucket=bucket, Key=key)

    def _check_credentials(self):
        if not self._creds_expiration:
            return

        expiration = parse_json_date(self._creds_expiration)

        if expiration < datetime.now(timezone.utc):
            new_creds = self._creds_getter()
            self._client = build_client(new_creds)
            self._creds_expiration = new_creds['Expiration']
