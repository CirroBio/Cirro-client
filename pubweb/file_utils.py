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
    root_directory = Path(directory)
    sizes = [f.stat().st_size for f in root_directory.glob('**/*') if f.is_file()]
    return {
        'size': f'{sum(sizes) / float(1 << 30):,.3f} GB',
        'numberOfFiles': len(sizes)
    }


def upload_directory(directory, s3_client, bucket, prefix):
    files = get_files_in_directory(directory)
    for file in files:
        key = f'{prefix}/{file}'
        local_path = str(Path(directory, file).as_posix())
        print(f"Uploading {file}")
        s3_client.upload_file(local_path, Bucket=bucket, Key=key)
