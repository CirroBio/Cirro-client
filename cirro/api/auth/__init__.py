from cirro.api.auth.base import AuthInfo
from cirro.api.auth.iam import IAMAuth
from cirro.api.auth.oauth_client import ClientAuth
from cirro.api.auth.username import UsernameAndPasswordAuth

__all__ = [
    'AuthInfo',
    'IAMAuth',
    'UsernameAndPasswordAuth',
    'ClientAuth',
    'get_auth_info_from_config'
]

from cirro.api.config import AppConfig


def get_auth_info_from_config(app_config: AppConfig):
    user_config = app_config.user_config
    if not user_config or not user_config.auth_method:
        return ClientAuth(region=app_config.region,
                          client_id=app_config.client_id,
                          auth_endpoint=app_config.auth_endpoint)

    auth_methods = [
        ClientAuth,
        UsernameAndPasswordAuth,
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
                          enable_cache=auth_config.get('enable_cache') == 'True')

    if matched_auth_method == IAMAuth and auth_config.get('load_current'):
        return IAMAuth.load_current()

    if matched_auth_method == IAMAuth:
        return IAMAuth(region=app_config.region, **auth_config)

    if matched_auth_method == UsernameAndPasswordAuth:
        return UsernameAndPasswordAuth(region=app_config.region,
                                       client_id=app_config.client_id,
                                       user_pool_id=app_config.user_pool_id,
                                       **auth_config)
