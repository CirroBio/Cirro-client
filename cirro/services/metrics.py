from typing import List

from cirro_api_client.v1.api.metrics import get_project_metrics, get_all_metrics
from cirro_api_client.v1.models import ProjectMetrics

from cirro.services.base import BaseService


class MetricsService(BaseService):
    """
    Service for interacting with the Metrics endpoints
    """
    def get_for_project(self, project_id: str) -> ProjectMetrics:
        """
        Retrieves the cost and storage metrics for a project.

        Args:
            project_id (str): ID of the Project
        """
        return get_project_metrics.sync(
            project_id=project_id,
            client=self._api_client
        )

    def get_all_metrics(self) -> List[ProjectMetrics]:
        """
        Retrieves all available metrics
        """
        return get_all_metrics.sync(client=self._api_client)
