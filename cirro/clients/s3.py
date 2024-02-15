import math
import threading
from pathlib import Path
from typing import Callable

from boto3 import Session
from botocore.config import Config
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
from cirro_api_client.v1.models import AWSCredentials
from tqdm import tqdm


def convert_size(size):
    if size == 0:
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size/p, 2)
    return '%.2f %s' % (s, size_name[i])


def format_creds_for_session(creds: AWSCredentials):
    return {
        'access_key': creds.access_key_id,
        'secret_key': creds.secret_access_key,
        'token': creds.session_token,
        'expiry_time': creds.expiration.isoformat()
    }


class ProgressPercentage:
    def __init__(self, progress: tqdm):
        self._lock = threading.Lock()
        self.progress = progress

    def __call__(self, bytes_amount):
        with self._lock:
            self.progress.update(bytes_amount)


class S3Client:
    def __init__(self, creds_getter: Callable[[], AWSCredentials], enable_additional_checksum=False):
        self._creds_getter = creds_getter
        self._client = self._build_session_client()
        self._upload_args = dict(ChecksumAlgorithm='SHA256') if enable_additional_checksum else dict()
        self._download_args = dict(ChecksumMode='ENABLED') if enable_additional_checksum else dict()

    def upload_file(self, local_path: Path, bucket: str, key: str):
        file_size = local_path.stat().st_size
        file_name = local_path.name

        with tqdm(total=file_size,
                  desc=f'Uploading file {file_name} ({convert_size(file_size)})',
                  bar_format="{desc} | {percentage:.1f}%|{bar:25} | {rate_fmt}",
                  unit='B', unit_scale=True,
                  unit_divisor=1024) as progress:
            absolute_path = str(local_path.absolute())
            self._client.upload_file(absolute_path, bucket, key,
                                     Callback=ProgressPercentage(progress),
                                     ExtraArgs=self._upload_args)

    def download_file(self, local_path: Path, bucket: str, key: str):
        file_size = self.get_file_stats(bucket, key)['ContentLength']
        file_name = local_path.name

        with tqdm(total=file_size,
                  desc=f'Downloading file {file_name} ({convert_size(file_size)})',
                  bar_format="{desc} | {percentage:.1f}%|{bar:25} | {rate_fmt}",
                  unit='B', unit_scale=True,
                  unit_divisor=1024) as progress:
            absolute_path = str(local_path.absolute())
            self._client.download_file(bucket, key, absolute_path,
                                       Callback=ProgressPercentage(progress),
                                       ExtraArgs=self._download_args)

    def create_object(self, bucket: str, key: str, contents: str, content_type: str):
        self._client.put_object(
            Bucket=bucket,
            Key=key,
            ContentType=content_type,
            ContentEncoding='utf-8',
            Body=bytes(contents, 'UTF-8'),
            **self._upload_args
        )

    def get_file(self, bucket: str, key: str) -> bytes:
        resp = self._client.get_object(Bucket=bucket, Key=key, **self._download_args)
        file_body = resp['Body']
        return file_body.read()

    def get_file_stats(self, bucket: str, key: str):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/head_object.html
        """
        return self._client.head_object(Bucket=bucket, Key=key)

    def _build_session_client(self):
        creds = self._creds_getter()

        if creds.expiration:
            session = get_session()
            session._credentials = RefreshableCredentials.create_from_metadata(
                metadata=format_creds_for_session(creds),
                refresh_using=self._refresh_credentials,
                method='sts'
            )
            session = Session(botocore_session=session)
        else:
            session = Session(
                aws_access_key_id=creds.access_key_id,
                aws_secret_access_key=creds.secret_access_key,
                aws_session_token=creds.session_token
            )
        s3_config = Config(
            use_dualstack_endpoint=True
        )
        return session.client('s3', region_name=creds.region, config=s3_config)

    def _refresh_credentials(self):
        new_creds = self._creds_getter()
        return format_creds_for_session(new_creds)
