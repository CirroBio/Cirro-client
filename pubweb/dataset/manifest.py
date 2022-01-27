import json
from functools import lru_cache
from pathlib import Path
from typing import List

from pubweb.dataset import Dataset


@lru_cache
def get_files_in_directory(directory):
    path = Path(directory)

    paths = []

    for file_path in path.rglob("*"):
        if file_path.is_dir():
            continue
        str_file_path = str(file_path)
        str_file_path = str_file_path.replace(f'{str(path)}/', "")
        paths.append(str_file_path)

    return paths


def get_directory_stats(directory):
    root_directory = Path(directory)
    sizes = [f.stat().st_size for f in root_directory.glob('**/*') if f.is_file()]
    return {
        'size': f'{sum(sizes) / float(1 << 30):,.3f} GB',
        'numberOfFiles': len(sizes)
    }


def save_manifest(dataset: Dataset, files: List[str], s3_client):
    manifest = {
        'name': dataset['name'],
        'desc': dataset['desc'],
        'process': dataset['process'],
        'project': dataset['project'],
        'files': [{'name': f} for f in files]
    }
    path = f'datasets/{dataset["id"]}/artifacts/manifest.json'
    s3_client.put_object(
        Bucket=f'z-{manifest["project"]}',
        Key=path,
        Body=json.dumps(manifest),
        ContentType='application/json'
    )
