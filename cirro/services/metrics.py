from cirro_api_client.v1.api.metrics import get_project_metrics

from cirro.services.base import BaseService


class MetricsService(BaseService):
    def get_for_project(self, project_id: str):
        """
        Retrieves metrics about a project.
        """
        return get_project_metrics.sync(project_id=project_id, client=self._api_client)
