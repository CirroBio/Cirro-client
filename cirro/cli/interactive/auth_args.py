from typing import Tuple, Dict

from cirro.api.auth import ClientAuth, UsernameAndPasswordAuth, IAMAuth
from cirro.cli.interactive.utils import ask, ask_yes_no


def gather_auth_config() -> Tuple[str, Dict]:
    auth_methods_map = {
        'Default authentication (recommended)': ClientAuth,
        'Username/password authentication (non-institutional)': UsernameAndPasswordAuth,
        'AWS IAM Credentials': IAMAuth
    }

    auth_method_answer = ask('select', 'Please select and authentication method',
                             choices=auth_methods_map.keys())

    auth_method = auth_methods_map[auth_method_answer]
    auth_method_config = {}

    if auth_method == UsernameAndPasswordAuth:
        auth_method_config['username'] = ask('text', 'Please enter your username', required=True)
        auth_method_config['password'] = ask('password', 'Please enter your password', required=True)

    if auth_method == ClientAuth:
        auth_method_config['enable_cache'] = ask_yes_no("Would you like to cache your login?")

    if auth_method == IAMAuth:
        if ask_yes_no("Would you like to manually specify AWS credentials?"):
            auth_method_config['access_key'] = ask('text', 'Please enter your access key ID', required=True)
            auth_method_config['secret_key'] = ask('text', 'Please enter your secret access key', required=True)
            auth_method_config['token'] = ask('text', 'Please enter your session token (optional)')
        else:
            auth_method_config['load_current'] = True

    return auth_method.__name__, auth_method_config
