from typing import List, Optional

from cirro_api_client.v1.api.references import get_reference_types, get_references_for_project
from cirro_api_client.v1.models import ReferenceType, Reference

from cirro.services.base import BaseService


class ReferenceService(BaseService):
    """
    Service for interacting with the References endpoints
    """
    def get_types(self) -> Optional[List[ReferenceType]]:
        """
        List available reference types
        """
        return get_reference_types.sync(client=self._api_client)

    def get_for_project(self, project_id: str) -> Optional[List[Reference]]:
        """
        List available references for a given project
        """
        return get_references_for_project.sync(project_id=project_id, client=self._api_client)
