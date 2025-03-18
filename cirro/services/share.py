from typing import List

from cirro_api_client.v1.api.sharing import get_shares, create_share, subscribe_share, unsubscribe_share, get_share, \
    update_share, delete_share
from cirro_api_client.v1.models import Share, ShareDetail, CreateResponse, ShareInput, ShareType

from cirro.services.base import BaseService


class ShareService(BaseService):
    """
    Service for interacting with the Share endpoints
    """

    def list(self, project_id: str, share_type: ShareType = None) -> List[Share]:
        """
        Retrieve a list of shares for a given project
        optionally filtered by share type

        Args:
            project_id (str): ID of the Project
            share_type (ShareType): Type of share to filter by

        ```python

        from cirro_api_client.v1.models import ShareType
        from cirro.cirro_client import CirroApi

        cirro = CirroApi()

        # List shares that we've published
        cirro.shares.list(project_id="project-id", share_type=ShareType.PUBLISHER)
        ```
        """
        shares = get_shares.sync(project_id=project_id, client=self._api_client)
        if share_type:
            shares = [share for share in shares if share.share_type == share_type]
        return shares

    def get(self, project_id: str, share_id: str) -> ShareDetail:
        """
        Get details of a share
        """
        return get_share.sync(project_id=project_id, share_id=share_id, client=self._api_client)

    def create(self, project_id: str, share: ShareInput) -> CreateResponse:
        """
        Publish a share for a given project
        """
        return create_share.sync(project_id=project_id,
                                 body=share,
                                 client=self._api_client)

    def update(self, project_id: str, share_id: str, share: ShareInput):
        """
        Publish a share for a given project
        """
        update_share.sync_detailed(project_id=project_id,
                                   share_id=share_id,
                                   body=share,
                                   client=self._api_client)

    def delete(self, project_id: str, share_id: str):
        """
        Delete a share
        """
        delete_share.sync_detailed(project_id=project_id,
                                   share_id=share_id,
                                   client=self._api_client)

    def subscribe(self, project_id: str, share_id: str):
        """
        Subscribe to a share for a given project
        """
        subscribe_share.sync_detailed(project_id=project_id,
                                      share_id=share_id,
                                      client=self._api_client)

    def unsubscribe(self, project_id: str, share_id: str):
        """
        Unsubscribe from a share for a given project
        """
        unsubscribe_share.sync_detailed(project_id=project_id,
                                        share_id=share_id,
                                        client=self._api_client)
