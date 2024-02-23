from cirro_api_client.v1.api.metrics import get_project_metrics
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
