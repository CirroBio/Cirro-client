import json
import os
from pathlib import Path, PurePath, PurePosixPath
from typing import List, Union

from boto3.exceptions import S3UploadFailedError

from pubweb.api.clients import S3Client, ApiClient
from pubweb.api.models.file import DirectoryStatistics, File, CheckDataTypesInput

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


def check_dataset_files(files: List[str], process_id: str, api_client: ApiClient, directory: str = ""):
    """
    Checks if the file mapping rules for a process are met by the list of files
    :param files: files to check
    :param process_id: ID for the process containing the file mapping rules
    :param api_client: api client
    :param directory: path to directory containing files
    """
    # add path to samplesheet in order to read it in later 
    files = [os.path.join(directory, file) if 'samplesheet.csv' in file else file for file in files]

    # Call pubweb function
    data_types_input = CheckDataTypesInput(fileNames=files, processId=process_id)
    query = '''
        query checkDataTypes($input: CheckDataTypesInput!) {
        checkDataTypes(input: $input)
        }
    '''
    resp = api_client.query(query, variables={'input': data_types_input})
    reqs = resp['checkDataTypes']

    # These will be samplesheet errors or no files errors
    if reqs['errorMsg']:
        raise ValueError(reqs['errorMsg'])
    
    # These will be error for missing files
    allowed_data_types = json.loads(reqs['allowedDataTypes'])
    all_errors = [entry['errorMsg'] for entry in allowed_data_types]
    patterns = [' or '.join([e['exampleName'] for e in entry['allowedPatterns']]) 
                for entry in allowed_data_types]

    if any(all_errors):
        raise ValueError("Files do not meet dataset type requirements. The expected files are: \n" +\
                         "\n".join(patterns))

    # TODO remove after testing
    raise ValueError('safety check so files dont upload - no errors actually raised')
