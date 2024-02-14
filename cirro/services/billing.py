from cirro_api_client.v1.api.billing import get_billing_accounts, update_billing_account
from cirro_api_client.v1.models import BillingAccountRequest

from cirro.services.base import BaseService


class BillingService(BaseService):
    def list(self):
        """
        Gets a list of billing accounts the current user has access to
        """
        return get_billing_accounts.sync(client=self._api_client)

    def update(self, billing_account_id: str, request: BillingAccountRequest):
        """
        Updates a billing account
        """
        update_billing_account.sync_detailed(billing_account_id=billing_account_id,
                                             body=request, client=self._api_client)
