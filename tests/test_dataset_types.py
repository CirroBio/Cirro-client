import os

import pytest

from pubweb.file_utils import check_dataset_files

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
DATA_PATH = os.path.join(__location__, 'data', 'dataset_types')

file_mapping_rules_list = [
    [{"glob": "*_*.{R1,R2}.fastq.gz",
      "sampleMatchingPattern": "(?P<sampleName>\\S*)_(?P<replicate>\\S*)\\.R(?P<read>\\S*)\\.fastq\\.gz",
      "description": "test"}],
    [{"glob": "*_*.{R1,R2}.fastq.gz",
      "description": "test"}],
    [{"sampleMatchingPattern": "(?P<sampleName>\\S*)_(?P<replicate>\\S*)\\.R(?P<read>\\S*)\\.fastq\\.gz",
      "description": "test"}]
]


@pytest.mark.parametrize("file_mapping_rules", file_mapping_rules_list)
def test_file_mapping_rules(file_mapping_rules):
    """
    Test that errors are raised when files don't match the dataset type's rules
    """
    with pytest.raises(ValueError) as e_info:
        check_dataset_files(files=["badmatch.fastq.gz"], file_mapping_rules=file_mapping_rules)
    assert "Files do not match dataset type." in str(e_info.value)


def test_no_file_mapping_rules():
    """Test that function doesn't error when no file mapping rules are available"""
    assert check_dataset_files(["test_test.R1.fastq.gz"], file_mapping_rules=None) is None


def test_samplesheet():
    """
    Test that samplesheet can be used to correct mismatched file names. Using MADDD-seq (FASTQ) rule.
    """
    file_mapping_rules = [{"glob": "*.fastq.gz", "min": 1, "description": "FASTQs"}]
    files = ['file1.gz',
             'file2.gz',
             'sampleSheet.csv'
             ]

    assert check_dataset_files(files, file_mapping_rules, directory=DATA_PATH) is None
