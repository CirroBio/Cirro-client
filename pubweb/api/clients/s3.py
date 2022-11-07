import math
import threading
from pathlib import Path
from typing import Callable

from boto3 import Session
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
from tqdm import tqdm

from pubweb.api.models.auth import Creds
from pubweb.utils import parse_json_date


def convert_size(size):
    if size == 0:
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size/p, 2)
    return '%.2f %s' % (s, size_name[i])


def format_creds_for_session(creds: Creds):
    expiration = parse_json_date(creds['Expiration'])
    return {
        'access_key': creds['AccessKeyId'],
        'secret_key': creds['SecretAccessKey'],
        'token': creds['SessionToken'],
        'expiry_time': expiration.isoformat()
    }


class ProgressPercentage:
    def __init__(self, progress: tqdm):
        self._lock = threading.Lock()
        self.progress = progress

    def __call__(self, bytes_amount):
        with self._lock:
            self.progress.update(bytes_amount)


class S3Client:
    def __init__(self, creds_getter: Callable[[], Creds]):
        self._creds_getter = creds_getter
        self._client = self._build_session_client()

    def upload_file(self, local_path: Path, bucket: str, key: str):
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
        file_size = self.get_file_stats(bucket, key)['ContentLength']
        file_name = local_path.name

        with tqdm(total=file_size,
                  desc=f'Downloading file {file_name} ({convert_size(file_size)})',
                  bar_format="{desc} | {percentage:.1f}%|{bar:25} | {rate_fmt}",
                  unit='B', unit_scale=True,
                  unit_divisor=1024) as progress:
            absolute_path = str(local_path.absolute())
            self._client.download_file(bucket, key, absolute_path, Callback=ProgressPercentage(progress))

    def create_object(self, bucket: str, key: str, contents: str, content_type: str):
        self._client.put_object(
            Bucket=bucket,
            Key=key,
            ContentType=content_type,
            ContentEncoding='utf-8',
            Body=bytes(contents, "UTF-8")
        )

    def get_file(self, bucket: str, key: str) -> bytes:
        resp = self._client.get_object(Bucket=bucket, Key=key)
        file_body = resp['Body']
        return file_body.read()

    def get_file_stats(self, bucket: str, key: str):
        return self._client.head_object(Bucket=bucket, Key=key)

    def _build_session_client(self):
        creds = self._creds_getter()

        if creds['Expiration']:
            session = get_session()
            session._credentials = RefreshableCredentials.create_from_metadata(
                metadata=format_creds_for_session(creds),
                refresh_using=self._refresh_credentials,
                method='sts'
            )
            session = Session(botocore_session=session)
        else:
            session = Session(
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken']
            )
        return session.client('s3')

    def _refresh_credentials(self):
        new_creds = self._creds_getter()
        return format_creds_for_session(new_creds)
