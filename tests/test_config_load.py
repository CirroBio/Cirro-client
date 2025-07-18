import os
import unittest

from cirro.config import AppConfig, extract_base_url

TEST_BASE_URL = "app.cirro.bio"


class TestConfigLoad(unittest.TestCase):
    @unittest.skipIf(
        os.environ.get('CI') == 'true',
        "Skipping test in CI environment."
    )
    def test_config_load(self):
        config = AppConfig(base_url=TEST_BASE_URL)
        self.assertIsNotNone(config.client_id)
        self.assertIsNotNone(config.auth_endpoint)

    def test_extract_base(self):
        test_cases = [
            f"https://{TEST_BASE_URL}",
            TEST_BASE_URL,
            f"https://{TEST_BASE_URL}/projects",
            f"{TEST_BASE_URL}/asd/",
        ]
        for test_case in test_cases:
            with self.subTest(test_case):
                self.assertEqual(TEST_BASE_URL, extract_base_url(test_case))
