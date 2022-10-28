import os
import unittest

from pubweb.file_utils import check_dataset_files

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
DATA_PATH = os.path.join(__location__, 'data', 'dataset_types')

file_mapping_rules_list = [
    ("Glob & Regex", [{"glob": "*_*.{R1,R2}.fastq.gz",
                       "sampleMatchingPattern":
                       "(?P<sampleName>\\S*)_(?P<replicate>\\S*)\\.R(?P<read>\\S*)\\.fastq\\.gz"}]),
    ("Glob Only", [{"glob": "*_*.{R1,R2}.fastq.gz"}])
]


class TestDatasetTypes(unittest.TestCase):
    def test_file_mapping_rules(self):
        """Checks if process file mapping rules are met for a list of files"""
        check_dataset_files(files=["good_match.R1.fastq.gz"], file_mapping_rules=file_mapping_rules_list[0][1])

    def test_file_mapping_rules_bad_match(self):
        """Test that errors are raised when files don't match the dataset type's rules, when
        the file_mapping_rules include both regex and glob, only regex, and only glob."""
        for test_name, file_mapping_rules in file_mapping_rules_list:
            with self.subTest(test_name):
                with self.assertRaises(ValueError) as context:
                    check_dataset_files(files=["badmatch.fastq.gz"], file_mapping_rules=file_mapping_rules)
            self.assertTrue("Files do not match dataset type." in str(context.exception))

    def test_no_file_mapping_rules(self):
        """Test that function doesn't error when no file mapping rules are available"""
        self.assertIsNone(check_dataset_files(["test_test.R1.fastq.gz"], file_mapping_rules=[]))
        self.assertIsNone(check_dataset_files(["test_test.R1.fastq.gz"], file_mapping_rules=None))

    def test_samplesheet(self):
        """
        Test that samplesheet can be used to correct mismatched file names.
        Using MADDD-seq (FASTQ) rule.
        """
        file_mapping_rules = [{"glob": "*.fastq.gz", "min": 1, "description": "FASTQs"}]
        files = ["file1.gz",
                 "file2.gz",
                 "sampleSheet.csv"
                 ]
        self.assertIsNone(check_dataset_files(files, file_mapping_rules, directory=DATA_PATH))


if __name__ == '__main__':
    unittest.main()
