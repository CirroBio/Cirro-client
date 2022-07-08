import json
import logging
import os
from pathlib import Path

import boto3
import pandas as pd

from pubweb.models.s3_path import S3Path


class PreprocessDataset:
    """
    Helper functions for performing preparatory tasks immediately before launching
    the analysis workflow for a dataset.
    """

    def __init__(self, s3_dataset: str):
        self.s3_dataset = s3_dataset
        self.files = self._read_csv(
            "config/files.csv",
            required_columns=["sample", "file"]
        )

        self.samplesheet = self._read_csv(
            "config/samplesheet.csv",
            required_columns=["sample"]
        )

        self.params = self._read_json(
            "config/params.json"
        )

        # Log to STDOUT
        log_formatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s [PreprocessDataset] %(message)s'
        )
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

    @classmethod
    def from_running(cls):
        """
        Creates a dataset instance from the currently running dataset
          expected to be called from the headnode
        """
        dataset_path = os.getenv("PW_S3_DATASET")
        return cls(dataset_path)

    def log(self):
        """Print logging messages about the dataset."""

        self.logger.info(f"Storage location for dataset: {self.s3_dataset}")
        self.logger.info(f"Number of files in dataset: {self.files.shape[0]:,}")
        self.logger.info(f"Number of samples in dataset: {self.samplesheet.shape[0]:,}")

    def _read_csv(self, suffix: str, required_columns=None) -> pd.DataFrame:
        """Read a CSV from the dataset and check for any required columns."""
        if required_columns is None:
            required_columns = []

        df = pd.read_csv(f"{self.s3_dataset}/{suffix}")
        for col in required_columns:
            assert col in df.columns.values, f"Did not find expected columns {col} in {self.s3_dataset}/{suffix}"
        return df

    def _read_json(self, suffix: str):
        """Read a JSON from the dataset"""

        # Make the full S3 path
        s3_path = S3Path(f"{self.s3_dataset}/{suffix}")

        # Open a connection to S3
        s3 = boto3.client('s3')

        # Read the object
        retr = s3.get_object(Bucket=s3_path.bucket, Key=s3_path.key)
        text = retr['Body'].read().decode()

        # Parse JSON
        return json.loads(text)

    def _write_json(self, dat, local_path: str, indent=4):
        with Path(local_path).open(mode="wt") as handle:
            return json.dump(dat, handle, indent=indent)

    def add_param(self, name: str, value, overwrite=False):
        """Add a parameter to the dataset."""

        assert overwrite or name not in self.params, \
            f"Cannot add parameter {name}, already exists (and overwrite=False)"

        self.logger.info(f"Adding parameter {name} = {value}")
        self.params[name] = value

        self.logger.info("Saving parameters")
        self._write_json(self.params, "nextflow.json")

    def remove_param(self, name: str, force=False):
        """Remove a parameter from the dataset."""

        assert force or name in self.params, \
            f"Cannot remove parameter {name}, does not exist (and force=False)"

        self.logger.info(f"Removing parameter {name}")
        del self.params[name]

        self.logger.info("Saving parameters")
        self._write_json(self.params, "nextflow.json")
