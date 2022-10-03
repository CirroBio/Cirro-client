# PubWeb Client

[![Build Python package](https://github.com/FredHutch/PubWeb-client/actions/workflows/package.yml/badge.svg)](https://github.com/FredHutch/PubWeb-client/actions/workflows/package.yml)
[![Lint and run tests](https://github.com/FredHutch/PubWeb-client/actions/workflows/lint.yml/badge.svg)](https://github.com/FredHutch/PubWeb-client/actions/workflows/lint.yml)
![](https://img.shields.io/pypi/v/pubweb.svg)

A Python 3.8+ library for the PubWeb platform.

## Installation and Set Up

You can install PubWeb using pip:

`pip install pubweb`

or by cloning the repository and running:

`python setup.py install`

Then run a one-time configuration of your login credentials in the command line by running:

`pubweb-cli configure`

This will ask you to select an authentication method. If you are a member of Fred Hutch or the University of Washington, select the default method which will give you a link to use to log through the browser. If you are not a member of those institutions, select the non-institutional authentication method and enter your Data Portal username and password into the command line when prompted.

Or if you'd prefer, you can configure in a Python session and run:
```
from pubweb import PubWeb
client = PubWeb()
```

which will give you a link to log in through the browser. 

## Command Line Usage

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

#### Listing datasets:
```bash
Usage: pubweb-cli list_datasets [OPTIONS]

  List available datasets

Options:
  --project TEXT         ID of the project
  --interactive          Gather arguments interactively
  --help                 Show this message and exit.
```

### Interactive Commands

When running a command, you can specify the `--interactive` flag to gather the command arguments interactively.

Example:

```bash
$ pubweb-cli upload --interactive
? What project is this dataset associated with?  Test project
? Enter the full path of the data directory  /shared/biodata/test
? Please confirm that you wish to upload 20 files (0.630 GB)  Yes
? What type of files?  Illumina Sequencing Run
? What is the name of this dataset?  test
? Enter a description of the dataset (optional)
? How would you like to upload or download your data? PubWeb CLI
```

## Python Usage

See the following set of Jupyter notebooks that contain examples on the following topics:

| Topic                            | Jupyter Notebook                                                    |
|----------------------------------|---------------------------------------------------------------------|
| Authenticating and installing    | [Introduction](samples/Getting_started.ipynb)                       |
| Uploading data                   | [Uploading a dataset](samples/Uploading_a_dataset.ipynb)            |
| Downloading data                 | [Downloading a dataset](samples/Downloading_a_dataset.ipynb)        |
| Calling data and reading into tables   | [Analyzing a dataset](samples/Interacting_with_files.ipynb)   |
| Running analysis pipelines       | [Analyzing a dataset](samples/Analyzing_a_dataset.ipynb)            |
| Managing reference data          | [Using references](samples/Using_references.ipynb)                  |
