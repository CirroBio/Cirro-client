import functools
import os
from pathlib import Path, PurePath, PurePosixPath
import re
from typing import List, Union

from boto3.exceptions import S3UploadFailedError
import pandas as pd

from pubweb.api.clients import S3Client
from pubweb.api.models.file import DirectoryStatistics, File

DEFAULT_TRANSFER_SPEED = 160


def filter_files_by_pattern(files: Union[List[File], List[str]], pattern: str) -> List[File]:
    """
    Filters a list of files by a glob pattern
    """
    def matches_glob(file: Union[File, str]):
        return PurePath(file if isinstance(file, str) else file.relative_path).match(pattern)

    return [
        file for file in files
        if matches_glob(file)
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


def check_samplesheet(files: List[str], samplesheet: str):
    """
    Check all files in samplesheet are unique and the list of files in the samplesheet
    and all the files in the samplesheet must be in the upload list
    :param files: files to check against the samplesheet, not including the samplesheet.csv file
    :param samplesheet: path and filename of samplesheet.csv file
    """
    df = pd.read_csv(samplesheet)
    cols = re.findall(r"fastq_[1|2]|file_\d+", ' '.join(df.columns))
    samplesheet_files = df[cols].values.flatten()

    if len(samplesheet_files) > len(set(samplesheet_files)):
        raise ValueError('The files in samplesheet.csv are not unique. Samplesheet is not valid.')

    missing_upload = set(samplesheet_files).difference(set(files))
    if missing_upload:
        raise FileNotFoundError("There are files in the samplesheet.csv file that are not included in the " +
                                "uploaded files. The following files are missing from the uploaded file list: \n" +
                                "\n".join(missing_upload))


def check_dataset_files(files: List[str], file_mapping_rules: Union[List[dict], None], directory: str = ""):
    """
    Checks if at least one of the file mapping rules for a process are met by at least one file
    in the list of files
    :param files: files to check
    :param file_mapping_rules: glob or sampleMatchingPattern (regex) rules to match against
    :param directory: path to directory containing files
    """
    if not file_mapping_rules or len(file_mapping_rules) == 0:
        return None

    if 'samplesheet.csv' in [file.lower() for file in files]:
        samplesheet_path = [file for file in files if 'samplesheet.csv' in file.lower()][0]
        files.remove(samplesheet_path)
        check_samplesheet(files, os.path.join(directory, samplesheet_path))
        return None

    def match_pattern(files, rule):
        matches_regex = any([re.match(rule['sampleMatchingPattern'], file) for file in files]) \
            if rule.get('sampleMatchingPattern') else False
        matches_glob = any([PurePosixPath(file).match(rule['glob']) for file in files]) if rule.get('glob') else False
        return matches_regex or matches_glob

    if not any(map(functools.partial(match_pattern, files), file_mapping_rules)):
        raise ValueError("Files do not match dataset type. Expected file type requirements: \n" + "\n".join(
            [f"{rule.get('description', '')} {rule.get('glob')}" for rule in file_mapping_rules]))
