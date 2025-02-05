from datetime import datetime

import jwt
from cirro_api_client import TokenAuth
from cirro_api_client.cirro_auth import AuthMethod

from cirro.auth.base import AuthInfo


class AccessTokenAuth(AuthInfo):
    """
    Authenticates to Cirro with a static access token

    :param token: Access token
    """

    def __init__(self, token: str):
        self._token = token
        self._username = None
        self._access_token_expiry = None
        self._update_token_metadata()

    def get_current_user(self) -> str:
        return self._username

    def get_auth_method(self) -> AuthMethod:
        return TokenAuth(token=self._token)

    def _update_token_metadata(self):
        decoded_access_token = jwt.decode(self._token,
                                          options={"verify_signature": False})
        self._access_token_expiry = datetime.fromtimestamp(decoded_access_token['exp'])
        self._username = decoded_access_token['username']
