import json
import logging
import os
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Union

import boto3

if TYPE_CHECKING:
    from pandas import DataFrame

from cirro.models.s3_path import S3Path

logger = logging.getLogger(__name__)


def _write_json(dat, local_path: str, indent=4):
    with Path(local_path).open(mode="wt") as handle:
        return json.dump(dat, handle, indent=indent)


def _read_csv(path: str, required_columns=None) -> 'DataFrame':
    """Read a CSV from the dataset and check for any required columns."""
    if required_columns is None:
        required_columns = []

    import pandas as pd
    df = pd.read_csv(path)
    for col in required_columns:
        assert col in df.columns.values, f"Did not find expected columns {col} in {path}"
    return df


def _read_json(path: str):
    """Read a JSON from the dataset"""

    s3_path = S3Path(path)

    if s3_path.valid:
        s3 = boto3.client('s3')
        retr = s3.get_object(Bucket=s3_path.bucket, Key=s3_path.key)
        text = retr['Body'].read().decode()
    else:
        with Path(path).open() as handle:
            text = handle.read()

    # Parse JSON
    return json.loads(text)


class PreprocessDataset:
    """
    Helper functions for performing preparatory tasks immediately before launching
    the analysis workflow for a dataset.
    """
    samplesheet: 'DataFrame'
    """
    A pandas DataFrame containing all of the metadata assigned to the samples present
    in the input datasets (at the time of analysis).

    More info: https://docs.cirro.bio/pipelines/preprocess-script/#dssamplesheet
    """
    files: 'DataFrame'
    """
    A DataFrame containing information on the files contained in the input datasets,
    and the sample that each file is assigned to.

    More info: https://docs.cirro.bio/pipelines/preprocess-script/#dsfiles
    """
    params: dict
    """
    A dictionary with all of the parameter values populated by user input
    using the process-form.json and process-input.json configurations.

    This is read-only, use `add_param` to add new parameters or `remove_param` to remove them.

    More info: https://docs.cirro.bio/pipelines/preprocess-script/#dsparams
    """
    metadata: dict
    """
    Detailed information about the dataset at the time of analysis,
    including the project, process, and input datasets.

    More info: https://docs.cirro.bio/pipelines/preprocess-script/#dsmetadata
    """

    def __init__(self,
                 samplesheet: Union['DataFrame', str],
                 files: Union['DataFrame', str],
                 params: dict,
                 metadata: dict):
        import pandas as pd
        # Convert DataFrame to string if necessary
        if isinstance(samplesheet, str):
            samplesheet = pd.read_csv(StringIO(samplesheet))
        if isinstance(files, str):
            files = pd.read_csv(StringIO(files))

        self.samplesheet = samplesheet
        self.files = files
        self.params = params
        self.metadata = metadata

    @classmethod
    def from_path(cls, dataset_root: str, config_directory='config'):
        """
        Creates an instance from a path
        (useful for testing or when running the script outside Cirro)
        """
        config_directory = Path(dataset_root, config_directory)

        files = _read_csv(
            str(Path(config_directory, "files.csv")),
            required_columns=["sample", "file"]
        )

        samplesheet = _read_csv(
            str(Path(config_directory, "samplesheet.csv")),
            required_columns=["sample"]
        )

        params = _read_json(
            str(Path(config_directory, "params.json")),
        )

        metadata = _read_json(
            str(Path(config_directory, "metadata.json")),
        )

        return cls(files=files, samplesheet=samplesheet, params=params, metadata=metadata)

    @classmethod
    def from_running(cls):
        """
        Creates an instance from the currently running dataset
        (expected to be called from inside a Cirro analysis process)
        """
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s [PreprocessDataset] %(message)s')
        dataset_path = os.getenv("PW_S3_DATASET")
        return cls.from_path(dataset_path)

    def log(self):
        """Print logging messages about the dataset."""
        logger.info(f"Number of files in dataset: {self.files.shape[0]:,}")
        logger.info(f"Number of samples in dataset: {self.samplesheet.shape[0]:,}")

    def add_param(self, name: str, value, overwrite=False, log=True):
        """Add a parameter to the dataset."""

        assert overwrite or name not in self.params, \
            f"Cannot add parameter {name}, already exists (and overwrite=False)"

        if log:
            logger.info(f"Adding parameter {name} = {value}")
        self.params[name] = value

        if log:
            logger.info("Saving parameters")
        _write_json(self.params, "nextflow.json")

    def remove_param(self, name: str, force=False):
        """Remove a parameter from the dataset."""

        assert force or name in self.params, \
            f"Cannot remove parameter {name}, does not exist (and force=False)"

        logger.info(f"Removing parameter {name}")
        if name in self.params:
            del self.params[name]

        logger.info("Saving parameters")
        _write_json(self.params, "nextflow.json")

    def update_compute(self, from_str, to_str, fp="nextflow-override.config"):
        """Replace all instances of a text string in the compute config file."""

        assert os.path.exists(fp), f"File does not exist: {fp}"
        with open(fp, 'r') as handle:
            compute = handle.read()
        n = len(compute.split(from_str)) - 1
        logger.info(f"Replacing {n:,} instances of {from_str} with {to_str} in {fp}")
        compute = compute.replace(from_str, to_str)
        with open(fp, 'wt') as handle:
            handle.write(compute)

    def wide_samplesheet(
            self,
            index=None,
            columns="read",
            values="file",
            column_prefix="fastq_"
    ):
        """Format a wide samplesheet with each read-pair on a row."""

        if index is None:
            index = ["sampleIndex", "sample", "lane"]
        logger.info("Formatting a wide samplesheet")
        logger.info("File table (long)")
        logger.info(self.files.head().to_csv(index=False))

        assert columns in self.files.columns.values, f"Column '{columns}' not found in file table"
        assert values in self.files.columns.values, f"Column '{values}' not found in file table"

        assert isinstance(index, list), f"index must be a list (not {type(index)})"

        # Get the list of columns from the inputs
        input_columns = self.files.columns.values

        # Format as a wide dataset
        # Note that all of the columns in `index` will be added if they are not already present
        wide_df = self.files.reindex(
            columns=index + [columns] + [values]
        ).pivot(
            index=index,
            columns=columns,
            values=values
        ).rename(
            columns=lambda i: f"{column_prefix}{int(i)}"
        ).reset_index(
        )

        # Remove any columns from the ouput which were added from `index`
        for cname in index:
            if cname not in input_columns:
                wide_df = wide_df.drop(columns=[cname])

        return wide_df
