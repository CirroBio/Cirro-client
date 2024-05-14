from cirro_api_client.v1.api.users import invite_user
from cirro_api_client.v1.models import InviteUserRequest

from cirro.services.base import BaseService


class UserService(BaseService):
    def invite_user(self, name: str, organization: str, email: str):
        """
        Invite a user to the system.
        If the user already exists, it will return a message that the user already exists.

        Args:
            name (str): Name of the user
            organization (str): Organization of the user
            email (str): Email (username) of the user
        """
        request = InviteUserRequest(
            name=name,
            organization=organization,
            email=email,
        )
        response = invite_user.sync(client=self._api_client, body=request)
        return response.message
