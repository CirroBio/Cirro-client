from pathlib import Path, PurePath
from typing import List

from boto3.exceptions import S3UploadFailedError

from pubweb.clients import S3Client
from pubweb.models.file import DirectoryStatistics

DEFAULT_TRANSFER_SPEED = 160


def filter_files_by_pattern(files: List[str], pattern: str) -> List[str]:
    """
    Filters a list of files by a glob pattern
    """
    return [
        file for file in files
        if PurePath(file).match(pattern)
    ]


def get_files_in_directory(directory) -> List[str]:
    path = Path(directory)
    path_posix = str(path.as_posix())

    paths = []

    for file_path in path.rglob("*"):
        if file_path.is_dir():
            continue
        str_file_path = str(file_path.as_posix())
        str_file_path = str_file_path.replace(f'{path_posix}/', "")
        paths.append(str_file_path)

    return paths


def get_directory_stats(directory) -> DirectoryStatistics:
    sizes = [f.stat().st_size for f in Path(directory).glob('**/*') if f.is_file()]
    total_size = sum(sizes) / float(1 << 30)
    return {
        'sizeFriendly': f'{total_size:,.3f} GB',
        'size': total_size,
        'numberOfFiles': len(sizes)
    }


def upload_directory(directory: str, files: List[str], s3_client: S3Client, bucket: str, prefix: str, max_retries=10):
    for file in files:
        key = f'{prefix}/{file}'
        local_path = Path(directory, file)
        success = False

        # Retry up to max_retries times
        for retry in range(max_retries):

            # Try the upload
            try:
                s3_client.upload_file(
                    local_path=local_path,
                    bucket=bucket,
                    key=key
                )

                success = True

            # Catch the upload error
            except S3UploadFailedError as e:

                # Report the error
                print(f"Encountered error:\n{str(e)}\nRetrying ({max_retries - (retry + 1)} attempts remaining)")

            if success:
                break


def download_directory(directory: str, files: List[str], s3_client: S3Client, bucket: str, prefix: str):
    for file in files:
        key = f'{prefix}/{file}'
        local_path = Path(directory, file)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        s3_client.download_file(local_path=local_path,
                                bucket=bucket,
                                key=key)


def estimate_token_lifetime(data_size_gb: float, speed_mbps: float = DEFAULT_TRANSFER_SPEED) -> int:
    """
    :param data_size_gb: Gigabytes
    :param speed_mbps: Megabits per second
    """
    transfer_time_seconds = (data_size_gb * 8 * 1000) / speed_mbps
    transfer_time_hours = transfer_time_seconds / 60 / 60
    return max(round(transfer_time_hours), 1)
