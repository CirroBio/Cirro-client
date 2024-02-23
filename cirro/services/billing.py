from typing import List

from cirro_api_client.v1.api.billing import get_billing_accounts, update_billing_account
from cirro_api_client.v1.models import BillingAccountRequest, BillingAccount

from cirro.services.base import BaseService


class BillingService(BaseService):
    """
    Service for interacting with the Billing endpoints
    """
    def list(self) -> List[BillingAccount]:
        """
        Gets a list of billing accounts the current user has access to
        """
        return get_billing_accounts.sync(client=self._api_client)

    def update(self, billing_account_id: str, request: BillingAccountRequest):
        """
        Updates a billing account

        Args:
            billing_account_id (str): Billing account ID
            request (cirro_api_client.v1.models.BillingAccountRequest):

        ```python
        from cirro_api_client.v1.models import BillingAccountRequest
        from cirro.cirro_client import CirroApi

        cirro = CirroApi()
        request = BillingAccountRequest(
            name="New billing account name",
            primary_budget_number="new-budget-number",
            owner="New Owner"
        )
        cirro.billing.update("billing-account-id", request)
        ```
        """
        update_billing_account.sync_detailed(
            billing_account_id=billing_account_id,
            body=request,
            client=self._api_client
        )
