from typing import TypedDict, Optional


class DeviceTokenResponse(TypedDict):
    device_code: str
    user_code: str
    verification_uri: str
    message: str
    interval: int
    expires_in: int
    expiry: str


class OAuthTokenResponse(TypedDict):
    access_token: str
    refresh_token: str
    id_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
    client_id: str
    message: Optional[str]
