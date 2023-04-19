import configparser
import os
from pathlib import Path
from typing import NamedTuple, Dict, Optional

import requests
from requests import HTTPError


class Constants:
    home = os.environ.get('PW_HOME', '~/.cirro')
    config_path = Path(home, 'config.ini').expanduser()
    default_base_url = "data-portal.io"
    default_max_retries = 10


class UserConfig(NamedTuple):
    auth_method: str
    auth_method_config: Dict  # This needs to match the init params of the auth method
    base_url: Optional[str]
    transfer_max_retries: Optional[int]


def save_user_config(user_config: UserConfig):
    original_user_config = load_user_config()
    ini_config = configparser.SafeConfigParser()
    ini_config['General'] = {
        'auth_method': user_config.auth_method,
        'base_url': Constants.default_base_url,
        'transfer_max_retries': Constants.default_max_retries
    }
    if original_user_config:
        ini_config['General']['base_url'] = original_user_config.base_url

    ini_config[user_config.auth_method] = user_config.auth_method_config
    Constants.config_path.parent.mkdir(exist_ok=True)
    with Constants.config_path.open('w') as configfile:
        ini_config.write(configfile)


def load_user_config() -> Optional[UserConfig]:
    if not Constants.config_path.exists():
        return None

    try:
        ini_config = configparser.ConfigParser()
        ini_config.read(str(Constants.config_path.absolute()))
        main_config = ini_config['General']
        auth_method = main_config.get('auth_method')
        base_url = main_config.get('base_url')
        transfer_max_retries = main_config.getint('transfer_max_retries', Constants.default_max_retries)

        if auth_method and ini_config.has_section(auth_method):
            auth_method_config = dict(ini_config[auth_method])
        else:
            auth_method_config = {}

        return UserConfig(
            auth_method=auth_method,
            auth_method_config=auth_method_config,
            base_url=base_url,
            transfer_max_retries=transfer_max_retries
        )
    except Exception:
        raise RuntimeError('Configuration load error, please re-run configuration')


class AppConfig:
    def __init__(self, base_url: str = None):
        self.user_config = load_user_config()
        self.base_url = (base_url or
                         os.environ.get('PW_BASE_URL') or
                         (self.user_config.base_url if self.user_config else None) or
                         Constants.default_base_url)
        self._init_config()

    def _init_config(self):
        self.rest_endpoint = f'https://api.{self.base_url}'
        self.auth_endpoint = f'https://api.{self.base_url}/auth'

        try:
            info_resp = requests.get(f'{self.rest_endpoint}/info/system')
            info_resp.raise_for_status()

            info = info_resp.json()
            self.client_id = info['auth']['sdkAppId']
            self.user_pool_id = info['auth']['userPoolId']
            self.references_bucket = info['referencesBucket']
            self.resources_bucket = info['resourcesBucket']
            self.data_endpoint = info['dataEndpoint']
            self.region = info['region']
        except HTTPError:
            raise RuntimeError('Failed to get system metadata')
