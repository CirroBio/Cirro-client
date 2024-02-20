import unittest

from cirro.config import AppConfig


class TestConfigLoad(unittest.TestCase):
    def test_config_load(self):
        config = AppConfig()
        self.assertIsNotNone(config.client_id)
        self.assertIsNotNone(config.auth_endpoint)
