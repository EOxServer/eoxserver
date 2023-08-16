import os
from unittest import mock

from django.test import TestCase

from eoxserver.core.config import get_eoxserver_config, reload_eoxserver_config


class TestConfig(TestCase):
    def test_config_interpolates_env_vars(self):
        new_url = "https://example.com/myows"
        # force reload because it's cached
        with mock.patch.dict(os.environ, {"HTTP_SERVICE_URL": new_url}):
            reload_eoxserver_config()
            current_config = get_eoxserver_config()

        self.assertEqual(
            current_config.get("services.owscommon", "http_service_url"),
            new_url,
        )

    def test_config_has_default_values(self):
        reload_eoxserver_config()
        current_config = get_eoxserver_config()
        self.assertEqual(
            current_config.get("services.owscommon", "http_service_url"),
            "http://localhost:8000/ows?",
        )
