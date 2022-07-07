# PubWeb Client

[![Build Python package](https://github.com/FredHutch/PubWeb-client/actions/workflows/package.yml/badge.svg)](https://github.com/FredHutch/PubWeb-client/actions/workflows/package.yml)
[![Lint and run tests](https://github.com/FredHutch/PubWeb-client/actions/workflows/lint.yml/badge.svg)](https://github.com/FredHutch/PubWeb-client/actions/workflows/lint.yml)
![](https://img.shields.io/pypi/v/pubweb.svg)

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

| Sample                                                               | Description                   |
|----------------------------------------------------------------------|-------------------------------|
| [01_Intro](samples/01_Intro.ipynb)                                   | Authenticating and installing |
| [02_Uploading_a_dataset](samples/02_Uploading_a_dataset.ipynb)       |                               |
| [03_Downloading_a_dataset](samples/03_Downloading_a_dataset.ipynb)   |                               |
| [04_Interacting_with_files](samples/04_Interacting_with_files.ipynb) |                               |
| [05_Analyzing_a_dataset](samples/05_Analyzing_a_dataset.ipynb)       |                               |
| [06_Using_references](samples/06_Using_references.ipynb)             | Managing reference data       |
