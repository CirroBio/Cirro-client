import os
import unittest

import pandas

from cirro.helpers.preprocess_dataset import PreprocessDataset

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
DATA_PATH = os.path.join(__location__, 'data')


class TestPreprocess(unittest.TestCase):
    def test_wide_samplesheet_1(self):
        ds = PreprocessDataset.from_path(DATA_PATH + '/example_data_1')
        df = ds.wide_samplesheet()

        expected_df = pandas.read_csv(DATA_PATH + '/example_data_1/expected_wide.csv')

        self.assertEqual(
            df.sort_index(axis=1).to_csv(index=None),
            expected_df.sort_index(axis=1).to_csv(index=False)
        )

    def test_wide_samplesheet_2(self):
        ds = PreprocessDataset.from_path(DATA_PATH + '/example_data_2')
        df = ds.wide_samplesheet()

        expected_df = pandas.read_csv(DATA_PATH + '/example_data_2/expected_wide.csv')

        self.assertEqual(
            df.sort_index(axis=1).to_csv(index=None),
            expected_df.sort_index(axis=1).to_csv(index=False)
        )


if __name__ == '__main__':
    unittest.main()
