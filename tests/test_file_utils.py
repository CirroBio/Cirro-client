import unittest
from pathlib import Path
from unittest.mock import Mock, call

from cirro.file_utils import upload_directory, get_files_in_directory, get_files_stats


class TestFileUtils(unittest.TestCase):
    def setUp(self):
        self.mock_s3_client = Mock()
        self.mock_s3_client.upload_file = Mock()
        self.test_bucket = 'project-1a1a'
        self.test_prefix = 'datasets/1a1a/data'

    def test_get_file_stats(self):
        files = get_files_in_directory(Path('.'))
        files = [Path(f) for f in files]
        stats = get_files_stats(files=files)
        self.assertGreater(stats.size, 0)
        self.assertGreater(stats.number_of_files, 0)
        self.assertIn('KiB', stats.size_friendly)

    def test_upload_directory_pathlike(self):
        test_path = Path('/Users/test/Documents/dataset1')
        test_files = [
            Path('/Users/test/Documents/dataset1/test_file.fastq'),
            Path('/Users/test/Documents/dataset1/folder1/test_file.fastq'),
        ]
        upload_directory(directory=test_path,
                         files=test_files,
                         s3_client=self.mock_s3_client,
                         bucket=self.test_bucket,
                         prefix=self.test_prefix)

        # The function should upload files relative to the directory path.
        self.mock_s3_client.upload_file.assert_has_calls([
            call(file_path=test_files[0], bucket=self.test_bucket, key=f'{self.test_prefix}/test_file.fastq'),
            call(file_path=test_files[1], bucket=self.test_bucket, key=f'{self.test_prefix}/folder1/test_file.fastq')
        ], any_order=True)

    def test_upload_directory_string(self):
        test_path = 'data'
        test_files = [
            'file1.txt',
            'folder1/file2.txt'
        ]
        upload_directory(directory=test_path,
                         files=test_files,
                         s3_client=self.mock_s3_client,
                         bucket=self.test_bucket,
                         prefix=self.test_prefix)

        # The function should upload files relative to the directory path,
        # but also format file_path into the Path object.
        self.mock_s3_client.upload_file.assert_has_calls([
            call(file_path=Path(test_path, test_files[0]),
                 bucket=self.test_bucket,
                 key=f'{self.test_prefix}/file1.txt'),
            call(file_path=Path(test_path, test_files[1]),
                 bucket=self.test_bucket,
                 key=f'{self.test_prefix}/folder1/file2.txt')
        ], any_order=True)

    def test_upload_directory_different_types(self):
        test_path = Path('s3://bucket/dataset1')
        test_files = [
            's3://bucket/dataset1/file2.txt'
        ]
        with self.assertRaises(ValueError):
            upload_directory(directory=test_path,
                             files=test_files,
                             s3_client=self.mock_s3_client,
                             bucket=self.test_bucket,
                             prefix=self.test_prefix)