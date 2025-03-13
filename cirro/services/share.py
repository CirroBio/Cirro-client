from typing import List

from cirro_api_client.v1.api.sharing import get_shares
from cirro_api_client.v1.models import Share

from cirro.services.base import BaseService


class ShareService(BaseService):
    """
    Service for interacting with the Share endpoints
    """

    def list(self, project_id: str) -> List[Share]:
        """
        Retrieve a list of shares
        """
        return get_shares.sync(project_id=project_id, client=self._api_client)
