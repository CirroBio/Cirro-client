# PubWeb Client

A Python 3.8+ library for the PubWeb platform.

## Installation

You can install PubWeb using pip

`pip install pubweb`

or by cloning the repo and running

`python setup.py install`

## Usage

### CLI Usage

Run `pubweb-cli configure` to configure your login credentials.

Specify the `--interactive` flag to gather the command arguments interactively. 

Example:

```bash
$ pubweb-cli upload --interactive
? What project is this dataset associated with?  Test project
? Enter the full path of the data directory  /shared/biodata/test
? Please confirm that you wish to upload 20 files (0.630 GB)  Yes
? What type of files?  Illumina Sequencing Run
? What is the name of this dataset?  test
? Enter a description of the dataset (optional)
```


#### Listing datasets:
```bash
Usage: pubweb-cli list_datasets [OPTIONS]

  List available datasets

Options:
  --project TEXT         ID of the project
  --interactive          Gather arguments interactively
  --help                 Show this message and exit.
```


#### Downloading a dataset:
```bash
Usage: pubweb-cli download [OPTIONS]

  Download dataset files

Options:
  --project TEXT         Name or ID of the project
  --dataset TEXT         ID of the dataset
  --data-directory TEXT  Directory to store the files
  --interactive          Gather arguments interactively
  --help                 Show this message and exit.
```

#### Uploading a dataset:
```bash
Usage: pubweb-cli upload [OPTIONS]

  Upload and create a dataset

Options:
  --name TEXT             Name of the dataset
  --description TEXT      Description of the dataset (optional)
  --project TEXT          Name or ID of the project
  --process TEXT          Name or ID of the ingest process
  --data-directory TEXT   Directory you wish to upload
  --interactive           Gather arguments interactively
  --use-third-party-tool  Use third party tool for upload (Generate manifest and one-time upload authentication token)
  --help                  Show this message and exit.
```

### SDK Usage

```python
from pubweb import PubWeb
from pubweb.auth import UsernameAndPasswordAuth, IAMAuth
from pubweb.models.dataset import CreateIngestDatasetInput
from pubweb.file_utils import filter_files_by_pattern

# Username / Password auth
client = PubWeb(auth_info=UsernameAndPasswordAuth("<username>", "<password>"))
# IAM Authentication
client = PubWeb(auth_info=IAMAuth.load_current())

project_id = '<project_id>'

# Creating a dataset & uploading files
dataset_create_request: CreateIngestDatasetInput = {
    'projectId': project_id,
    'processId': 'sequencing-run',
    'name': 'Test dataset',
    'description': '',
    'files': [
        'image.jpg'
    ]
}

create_response = client.dataset.create(dataset_create_request)

directory_to_upload = '/fh/fast/test'

client.dataset.upload_files(
    project_id=project_id,
    dataset_id=create_response['datasetId'],
    directory=directory_to_upload,
    files=dataset_create_request['files']
)


# Downloading files
datasets = client.dataset.find_by_project(project_id)
dataset_id = datasets[0]['id']

files = client.dataset.get_dataset_files(project_id=project_id,
                                         dataset_id=dataset_id)
files = filter_files_by_pattern(files, '*.csv')

# Files is an optional parameter, if you omit it, it will download all the dataset files
client.dataset.download_files(project_id=project_id,
                              dataset_id=dataset_id,
                              download_location='/tmp',
                              files=files)
```

### Development

Building

```
python setup.py bdist_wheel
twine upload dist/*
```