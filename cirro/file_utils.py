import os
import random
import time
from pathlib import Path, PurePath
from typing import List, Union

from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ConnectionError

from cirro.clients import S3Client
from cirro.models.file import DirectoryStatistics, File

if os.name == 'nt':
    import win32api
    import win32con


def filter_files_by_pattern(files: Union[List[File], List[str]], pattern: str) -> Union[List[File], List[str]]:
    """
    Filters a list of files by a glob pattern

    Args:
        files (Union[List[File], List[str]]): List of Files or file paths
        pattern (str): Glob pattern (i.e., *.fastq)

    Returns:
        The filtered list of files
    """
    def matches_glob(file: Union[File, str]):
        return PurePath(file if isinstance(file, str) else file.relative_path).match(pattern)

    return [
        file for file in files
        if matches_glob(file)
    ]


def _is_hidden_file(file_path: Path):
    # Remove hidden files from listing, desktop.ini .DS_Store, etc.
    if os.name == 'nt':
        attributes = win32api.GetFileAttributes(str(file_path))
        return attributes & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        return file_path.name.startswith('.')


def get_files_in_directory(
    directory: Union[str, Path],
    include_hidden=False
) -> List[str]:
    """
    Returns a list of strings containing the relative path of
    each file within the indicated directory.

    Args:
        directory (Union[str, Path]): The path to the directory
        include_hidden (bool): include hidden files in the returned list

    Returns:
        List of files in the directory
    """
    path = Path(directory).expanduser()
    path_posix = str(path.as_posix())

    paths = []

    for file_path in path.rglob("*"):
        if file_path.is_dir():
            continue

        if not include_hidden and _is_hidden_file(file_path):
            continue

        if not file_path.exists():
            continue

        str_file_path = str(file_path.as_posix())
        str_file_path = str_file_path.replace(f'{path_posix}/', "")
        paths.append(str_file_path)

    paths.sort()
    return paths


def get_files_stats(files: List[Path]) -> DirectoryStatistics:
    """
    @private
    """
    sizes = [f.stat().st_size for f in files]
    total_size = sum(sizes) / float(1 << 30)
    return {
        'sizeFriendly': f'{total_size:,.3f} GB',
        'size': total_size,
        'numberOfFiles': len(sizes)
    }


def upload_directory(directory: str, files: List[str], s3_client: S3Client, bucket: str, prefix: str, max_retries=10):
    """
    @private
    """
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
            except (S3UploadFailedError, ConnectionError) as e:
                delay = random.uniform(0, 60) + retry * 60
                # Report the error
                print(f"Encountered error:\n{str(e)}\n"
                      f"Retrying in {delay:.0f} seconds ({max_retries - (retry + 1)} attempts remaining)")
                time.sleep(delay)

            if success:
                break


def download_directory(directory: str, files: List[str], s3_client: S3Client, bucket: str, prefix: str):
    """
    @private
    """
    for file in files:
        key = f'{prefix}/{file}'.lstrip('/')
        local_path = Path(directory, file)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        s3_client.download_file(local_path=local_path,
                                bucket=bucket,
                                key=key)
