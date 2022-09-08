import configparser
import os
from pathlib import Path
from typing import NamedTuple

PUBWEB_CONFIG_LOCATION = "~/.pubweb/config"


class AuthConfig(NamedTuple):
    username: str
    password: str


class DevelopmentConfig:
    user_pool_id = 'us-west-2_ViB3UFcvp'
    app_id = '39jl0uud4d1i337q7gc5l03r98'
    data_endpoint = 'https://drdt2z4kljdbte5s4zx623kyk4.appsync-api.us-west-2.amazonaws.com/graphql'
    region = 'us-west-2'
    resources_bucket = 'pubweb-resources-dev'
    base_url = "https://dev.pubweb.cloud"


class ProductionConfig:
    user_pool_id = 'us-west-2_LQnstneoZ'
    app_id = '2seju0a0p55hmdajb61ftm4edc'
    data_endpoint = 'https://22boctowkfbuzaidvbvwjxfnai.appsync-api.us-west-2.amazonaws.com/graphql'
    region = 'us-west-2'
    resources_bucket = 'pubweb-resources-prd'
    base_url = "https://pubweb.cloud"


if os.environ.get('ENV', '').upper() == 'DEV':
    config = DevelopmentConfig()
else:
    config = ProductionConfig()


def get_config_path() -> Path:
    config_location = os.environ.get('PW_CONFIG', PUBWEB_CONFIG_LOCATION)
    return Path(config_location).expanduser()


def save_config(auth_config: AuthConfig):
    ini_config = configparser.SafeConfigParser()
    ini_config['DEFAULT'] = auth_config._asdict()
    config_path = get_config_path()
    config_path.parent.mkdir(exist_ok=True)
    with config_path.open('w') as configfile:
        ini_config.write(configfile)


def load_config() -> AuthConfig:
    config_path = get_config_path()
    if not config_path.exists():
        raise RuntimeError('Please configure authentication by running pubweb-cli configure')
    ini_config = configparser.ConfigParser()
    ini_config.read(str(config_path.absolute()))
    auth_config = ini_config['DEFAULT']
    return AuthConfig(auth_config['username'], auth_config['password'])
