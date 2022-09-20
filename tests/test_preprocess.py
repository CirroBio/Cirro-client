import unittest

import pandas

from pubweb.helpers.preprocess_dataset import PreprocessDataset


class TestPreprocess(unittest.TestCase):
    def test_something(self):
        ds = PreprocessDataset('example_data', '')
        df = ds.wide_samplesheet()

        expected_df = pandas.read_csv('example_data/expected_wide.csv')
        self.assertEqual(df, expected_df)


if __name__ == '__main__':
    unittest.main()
