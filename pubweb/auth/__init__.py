from pubweb.auth.base import AuthInfo
from pubweb.auth.iam import IAMAuth
from pubweb.auth.oauth_client import ClientAuth
from pubweb.auth.username import UsernameAndPasswordAuth
from pubweb.config import config


__all__ = [
    'AuthInfo',
    'IAMAuth',
    'UsernameAndPasswordAuth',
    'ClientAuth',
    'get_auth_info_from_config'
]
default_auth_method = ClientAuth


def get_auth_info_from_config():
    user_config = config.user_config

    if not user_config or not user_config.auth_method:
        return default_auth_method()

    auth_methods = [
        ClientAuth,
        UsernameAndPasswordAuth,
        IAMAuth
    ]
    matched_auth_method = next((m for m in auth_methods if m.__name__ == user_config.auth_method), None)
    if not matched_auth_method:
        raise RuntimeError(f'{user_config.auth_method} not found, please re-run configuration')

    try:
        auth_config = user_config.auth_method_config

        if isinstance(matched_auth_method, IAMAuth) and auth_config.get('load_current'):
            return IAMAuth.load_current()

        return matched_auth_method(**auth_config)
    except Exception:
        raise RuntimeError('Auth method load error, please re-run configuration')
