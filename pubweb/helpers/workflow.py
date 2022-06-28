import json
import os
from pathlib import Path

import pandas as pd


class RunningWorkflowHelper:
    """
    Could be a better name
    Provides common utility methods for running workflows
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

    @classmethod
    def from_running(cls):
        """
        Creates a workflow
        :return:
        """
        dataset_path = os.getenv("PW_S3_DATASET")
        return cls(dataset_path)

    def log(self):
        """Print logging messages about the dataset."""

        print(f"Storage location for dataset: {self.s3_dataset}")
        print(f"Number of files in dataset: {self.files.shape[0]:,}")
        print(f"Number of samples in dataset: {self.samplesheet.shape[0]:,}")

    def _read_csv(self, suffix: str, required_columns=None) -> pd.DataFrame:
        """Read a CSV from the dataset and check for any required columns."""
        if required_columns is None:
            required_columns = []

        df = pd.read_csv(f"{self.s3_dataset}/{suffix}")
        for col in required_columns:
            assert col in df.columns.values, f"Did not find expected columns {col} in {self.s3_dataset}/{suffix}"
        return df

    def _read_json(self, suffix: str):
        with Path(f'{self.s3_dataset}/{suffix}').open() as handle:
            return json.load(handle)
