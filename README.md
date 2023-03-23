# Cirro Client

[![Build Python package](https://github.com/FredHutch/Cirro-client/actions/workflows/package.yml/badge.svg)](https://github.com/FredHutch/Cirro-client/actions/workflows/package.yml)
[![Lint and run tests](https://github.com/FredHutch/Cirro-client/actions/workflows/lint.yml/badge.svg)](https://github.com/FredHutch/Cirro-client/actions/workflows/lint.yml)
![](https://img.shields.io/pypi/v/cirro.svg)

A Python 3.8+ library for the Cirro platform.

## Installation

You can install Cirro using pip:

`pip install cirro`

or by cloning the repository and running:

`python setup.py install`

## Set Up
Run a one-time configuration of your login credentials in the command line using:

`cirro-cli configure`

 This will ask you to select an authentication method. If you are a member of Fred Hutch or the University of Washington, select the default method which will give you a link to use to log through the browser. If you are not a member of those institutions, select the non-institutional authentication method and enter your Data Portal username and password into the command line when prompted.


## Command Line Usage

#### Downloading a dataset:
```bash
Usage: cirro-cli download [OPTIONS]

  Download dataset files

Options:
  --project TEXT         Name or ID of the project
  --dataset TEXT         ID of the dataset
  --data-directory TEXT  Directory to store the files
  -i, --interactive      Gather arguments interactively
  --help                 Show this message and exit.
```

#### Uploading a dataset:
```bash
Usage: cirro-cli upload [OPTIONS]

  Upload and create a dataset

Options:
  --name TEXT             Name of the dataset
  --description TEXT      Description of the dataset (optional)
  --project TEXT          Name or ID of the project
  --process TEXT          Name or ID of the ingest process
  --data-directory TEXT   Directory you wish to upload
  -i, --interactive       Gather arguments interactively
  --help                  Show this message and exit.
```

#### Listing datasets:
```bash
Usage: cirro-cli list-datasets [OPTIONS]

  List available datasets

Options:
  --project TEXT         ID of the project
  -i, --interactive      Gather arguments interactively
  --help                 Show this message and exit.
```

### Interactive Commands

When running a command, you can specify the `--interactive` flag to gather the command arguments interactively.

Example:

```bash
$ cirro-cli upload --interactive
? What project is this dataset associated with?  Test project
? Enter the full path of the data directory  /shared/biodata/test
? Please confirm that you wish to upload 20 files (0.630 GB)  Yes
? What type of files?  Illumina Sequencing Run
? What is the name of this dataset?  test
? Enter a description of the dataset (optional)
```

## Python Usage

See the following set of Jupyter notebooks that contain examples on the following topics:

| Jupyter Notebook                                                   | Topic                                |
|--------------------------------------------------------------------|--------------------------------------|
| [Introduction](samples/Getting_started.ipynb)                      | Installing and authenticating        |
| [Uploading a dataset](samples/Uploading_a_dataset.ipynb)           | Uploading data                       |
| [Downloading a dataset](samples/Downloading_a_dataset.ipynb)       | Downloading data                     |
| [Interacting with a dataset](samples/Interacting_with_files.ipynb) | Calling data and reading into tables |
| [Analyzing a dataset](samples/Analyzing_a_dataset.ipynb)           | Running analysis pipelines           |
| [Using references](samples/Using_references.ipynb)                 | Managing reference data              |

## R Usage

| Jupyter Notebook                                    | Topic               |
|-----------------------------------------------------|---------------------|
| [Downloading a dataset in R](samples/Using-R.ipynb) | Reading data with R |

## Advanced Usage

### Supported environment variables

| Name        | Description                   | Default         |
|-------------|-------------------------------|-----------------|
| PW_HOME     | Local configuration directory | ~/.cirro        |
| PW_BASE_URL | Base URL of the data portal   | data-portal.io  |

### Configuration

The `cirro-cli configure` command creates a file in `PW_HOME` called `config.ini`.

You can set the `base_url` property in the config file rather than using the environment variable. 

```ini
[General]
base_url = data-portal.io
```