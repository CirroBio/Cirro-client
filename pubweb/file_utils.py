import math
from functools import lru_cache
from pathlib import Path
from typing import List


@lru_cache
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


def convert_size(size):
    if size == 0:
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size/p, 2)
    return '%.2f %s' % (s, size_name[i])


def upload_directory(directory, s3_client, bucket, prefix):
    files = get_files_in_directory(directory)
    for file in files:
        key = f'{prefix}/{file}'
        local_path = Path(directory, file)
        local_path_normalized = str(local_path.as_posix())
        file_size = local_path.stat().st_size
        print(f'Uploading file {file} ({convert_size(file_size)})')

        s3_client.upload_file(local_path_normalized,
                              Bucket=bucket,
                              Key=key)


def download_directory(directory, s3_client, bucket, prefix, files):
    for file in files:
        key = f'{prefix}/{file}'
        local_path = str(Path(directory, file).as_posix())
        # head_resp = s3_client.head_object(Bucket=bucket, Key=key)
        # file_size = head_resp['ContentLength']
        print(f'Downloading file {file}')
        s3_client.download_file(bucket, key, local_path)
