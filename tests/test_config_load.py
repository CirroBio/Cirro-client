import unittest

from cirro.config import AppConfig, list_tenants, extract_base_url

TEST_BASE_URL = "app.cirro.bio"


class TestConfigLoad(unittest.TestCase):
    def test_config_load(self):
        config = AppConfig(base_url=TEST_BASE_URL)
        self.assertIsNotNone(config.client_id)
        self.assertIsNotNone(config.auth_endpoint)

    def test_list_tenants(self):
        tenants = list_tenants()
        self.assertGreater(len(tenants), 1)

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
