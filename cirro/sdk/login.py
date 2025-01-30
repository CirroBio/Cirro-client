from cirro.auth import DeviceCodeAuth
from cirro.cirro_client import CirroApi
from cirro.config import AppConfig
from cirro.sdk.portal import DataPortal


class DataPortalLogin:
    """
    Start the login process, obtaining the authorization message from Cirro
    needed to confirm the user identity.

    Useful when you need to authenticate a user in a non-blocking way.

    Usage:

    ```python
    # Replace app.cirro.bio as appropriate
    login = DataPortalLogin(base_url="app.cirro.bio")

    # Present the user with the authorization message
    print(login.auth_message)

    # Generate the authenticated DataPortal object,
    # blocking until the user completes the login process in their browser
    portal = login.await_completion()
    ```
    """
    base_url: str
    auth_info: DeviceCodeAuth

    def __init__(self, base_url: str = None, enable_cache=False):
        app_config = AppConfig(base_url=base_url)

        self.auth_info = DeviceCodeAuth(
            region=app_config.region,
            client_id=app_config.client_id,
            auth_endpoint=app_config.auth_endpoint,
            enable_cache=enable_cache,
            await_completion=False
        )

    @property
    def auth_message(self) -> str:
        """Authorization message provided by Cirro."""
        return self.auth_info.auth_message

    @property
    def auth_message_markdown(self) -> str:
        """Authorization message provided by Cirro (Markdown format)."""
        return self.auth_info.auth_message_markdown

    def await_completion(self) -> DataPortal:
        """Complete the login process and return an authenticated client"""

        # Block until the user completes the login flow
        self.auth_info.await_completion()

        # Set up the client object
        cirro_client = CirroApi(
            auth_info=self.auth_info,
            base_url=self.base_url
        )

        # Return the Data Portal object
        return DataPortal(client=cirro_client)
