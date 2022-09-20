import unittest

import pandas

from pubweb.helpers.preprocess_dataset import PreprocessDataset


class TestPreprocess(unittest.TestCase):
    def test_wide_samplesheet_1(self):
        ds = PreprocessDataset('example_data_1')
        df = ds.wide_samplesheet()

        expected_df = pandas.read_csv('example_data_1/expected_wide.csv')

        self.assertEqual(
            df.sort_index(axis=1).to_csv(index=None),
            expected_df.sort_index(axis=1).to_csv(index=None)
        )

    def test_wide_samplesheet_2(self):
        ds = PreprocessDataset('example_data_2')
        df = ds.wide_samplesheet()


        expected_df = pandas.read_csv('example_data_2/expected_wide.csv')

        self.assertEqual(
            df.sort_index(axis=1).to_csv(index=None),
            expected_df.sort_index(axis=1).to_csv(index=None)
        )


if __name__ == '__main__':
    unittest.main()
