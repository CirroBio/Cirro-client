from typing import List

from cirro_api_client.v1.api.compute_environment import get_compute_environments
from cirro_api_client.v1.models import ComputeEnvironmentConfiguration

from cirro.services.base import BaseService


class ComputeEnvironmentService(BaseService):
    """
    Service for interacting with the Compute Environment endpoints
    """

    def list_environments_for_project(self, project_id: str) -> List[ComputeEnvironmentConfiguration]:
        """
        List of custom compute environments for a project (i.e., an agent)

        Args:
            project_id (str): Project ID

        Returns:
            List of compute environments that are available for the project
        """
        return get_compute_environments.sync(project_id=project_id,
                                             client=self._api_client)
