from cirro_api_client import CirroApiClient

from cirro.auth import get_auth_info_from_config
from cirro.auth.base import AuthInfo
from cirro.config import AppConfig
from cirro.services.billing import BillingService
from cirro.services.dataset import DatasetService
from cirro.services.execution import ExecutionService
from cirro.services.file import FileService
from cirro.services.metadata import MetadataService
from cirro.services.metrics import MetricsService
from cirro.services.process import ProcessService
from cirro.services.projects import ProjectService


class Cirro:
    """
    Client for interacting with Cirro
    """
    def __init__(self, auth_info: AuthInfo = None, base_url: str = None):
        self._configuration = AppConfig(base_url=base_url)
        if not auth_info:
            auth_info = get_auth_info_from_config(self._configuration, auth_io=None)

        self._api_client = CirroApiClient(
            base_url=self._configuration.rest_endpoint,
            auth_method=auth_info.get_auth_method()
        )
        self._api_client._client_name = 'CirroSDK'
        self._api_client_package_name = 'cirro'

        # Init services
        self._file_service = FileService(self._api_client,
                                         enable_additional_checksum=self._configuration.enable_additional_checksum,
                                         transfer_retries=self._configuration.transfer_max_retries)
        self._dataset_service = DatasetService(self._api_client, file_service=self._file_service)
        self._project_service = ProjectService(self._api_client)
        self._process_service = ProcessService(self._api_client)
        self._execution_service = ExecutionService(self._api_client)
        self._metrics_service = MetricsService(self._api_client)
        self._metadata_service = MetadataService(self._api_client)
        self._billing_service = BillingService(self._api_client)

    @property
    def datasets(self):
        return self._dataset_service

    @property
    def projects(self):
        return self._project_service

    @property
    def processes(self):
        return self._process_service

    @property
    def execution(self):
        return self._execution_service

    @property
    def metrics(self):
        return self._metrics_service

    @property
    def metadata(self):
        return self._metadata_service

    @property
    def billing(self):
        return self._billing_service

    @property
    def api_client(self):
        """
        Gets the underlying API client
        """
        return self._api_client
