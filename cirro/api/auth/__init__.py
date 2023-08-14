from io import StringIO
from typing import Optional
from cirro.api.auth.base import AuthInfo
from cirro.api.auth.iam import IAMAuth
from cirro.api.auth.oauth_client import ClientAuth

__all__ = [
    'AuthInfo',
    'IAMAuth',
    'ClientAuth',
    'get_auth_info_from_config'
]

from cirro.api.config import AppConfig


def get_auth_info_from_config(app_config: AppConfig, auth_io: Optional[StringIO] = None):
    user_config = app_config.user_config
    if not user_config or not user_config.auth_method:
        return ClientAuth(region=app_config.region,
                          client_id=app_config.client_id,
                          auth_endpoint=app_config.auth_endpoint,
                          auth_io=auth_io)

    auth_methods = [
        ClientAuth,
        IAMAuth
    ]
    matched_auth_method = next((m for m in auth_methods if m.__name__ == user_config.auth_method), None)
    if not matched_auth_method:
        raise RuntimeError(f'{user_config.auth_method} not found, please re-run configuration')

    auth_config = user_config.auth_method_config

    if matched_auth_method == ClientAuth:
        return ClientAuth(region=app_config.region,
                          client_id=app_config.client_id,
                          auth_endpoint=app_config.auth_endpoint,
                          enable_cache=auth_config.get('enable_cache') == 'True',
                          auth_io=auth_io)

    if matched_auth_method == IAMAuth and auth_config.get('load_current'):
        return IAMAuth.load_current()

    if matched_auth_method == IAMAuth:
        return IAMAuth(region=app_config.region, **auth_config)
