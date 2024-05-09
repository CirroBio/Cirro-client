import unittest

from cirro.config import AppConfig, list_tenants


class TestConfigLoad(unittest.TestCase):
    def test_config_load(self):
        config = AppConfig(base_url="app.cirro.bio")
        self.assertIsNotNone(config.client_id)
        self.assertIsNotNone(config.auth_endpoint)

    def test_list_tenants(self):
        tenants = list_tenants()
        self.assertGreater(len(tenants), 1)