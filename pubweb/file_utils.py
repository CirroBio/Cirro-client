from boto3.exceptions import S3UploadFailedError
from pathlib import Path
from typing import List

from pubweb.clients import S3Client


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


def get_directory_stats(directory):
    sizes = [f.stat().st_size for f in Path(directory).glob('**/*') if f.is_file()]
    return {
        'size': f'{sum(sizes) / float(1 << 30):,.3f} GB',
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


def download_directory(directory: str, s3_client: S3Client, bucket: str, prefix: str, files: List[str]):
    for file in files:
        key = f'{prefix}/{file}'
        local_path = Path(directory, file)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        s3_client.download_file(local_path=local_path,
                                bucket=bucket,
                                key=key)
