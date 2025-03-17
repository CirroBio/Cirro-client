from typing import List

from cirro_api_client.v1.api.sharing import get_shares, create_share, subscribe_share, unsubscribe_share
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

    def create(self, project_id: str):
        """
        Create a new share
        """
        return create_share.sync(project_id=project_id, client=self._api_client)

    def subscribe(self, project_id: str, share_id: str):
        subscribe_share.sync_detailed(project_id=project_id, share_id=share_id, client=self._api_client)

    def unsubscribe(self, project_id: str, share_id: str):
        unsubscribe_share.sync_detailed(project_id=project_id, share_id=share_id, client=self._api_client)
