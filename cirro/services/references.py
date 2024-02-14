from cirro_api_client.v1.api.references import get_reference_types, get_references_for_project

from cirro.services.base import BaseService


class ReferenceService(BaseService):
    def get_types(self):
        """
        List available reference types
        """
        return get_reference_types.sync(client=self._api_client)

    def get_for_project(self, project_id: str):
        """
        List available references for a given project
        """
        return get_references_for_project.sync(project_id=project_id, client=self._api_client)
