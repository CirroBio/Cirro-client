import configparser
import os
from pathlib import Path
from typing import NamedTuple, Dict, Optional

PUBWEB_HOME = os.environ.get('PW_HOME', '~/.pubweb')
config_path = Path(PUBWEB_HOME, 'config.ini').expanduser()


class UserConfig(NamedTuple):
    auth_method: str
    auth_method_config: Dict  # This needs to match the init params of the auth method


def save_user_config(user_config: UserConfig):
    ini_config = configparser.SafeConfigParser()
    ini_config['General'] = {
        'auth_method': user_config.auth_method
    }
    ini_config[user_config.auth_method] = user_config.auth_method_config
    config_path.parent.mkdir(exist_ok=True)
    with config_path.open('w') as configfile:
        ini_config.write(configfile)


def load_user_config() -> Optional[UserConfig]:
    if not config_path.exists():
        return None

    try:
        ini_config = configparser.ConfigParser()
        ini_config.read(str(config_path.absolute()))
        main_config = ini_config['General']
        auth_method = main_config.get('auth_method')

        if auth_method and ini_config.has_section(auth_method):
            auth_method_config = dict(ini_config[auth_method])
        else:
            auth_method_config = {}

        return UserConfig(
            auth_method=auth_method,
            auth_method_config=auth_method_config
        )
    except Exception:
        raise RuntimeError('Configuration load error, please re-run configuration')


class BaseConfig:
    home = PUBWEB_HOME
    user_config = load_user_config()


# TODO: Get this from a metadata API by specifying the base URL
class DevelopmentConfig(BaseConfig):
    user_pool_id = 'us-west-2_ViB3UFcvp'
    app_id = '39jl0uud4d1i337q7gc5l03r98'
    data_endpoint = 'https://drdt2z4kljdbte5s4zx623kyk4.appsync-api.us-west-2.amazonaws.com/graphql'
    rest_endpoint = 'https://3b71dp5mn2.execute-api.us-west-2.amazonaws.com/dev'
    region = 'us-west-2'
    resources_bucket = 'pubweb-resources-dev'
    references_bucket = 'pubweb-resources'
    base_url = 'https://dev.pubweb.cloud'


class ProductionConfig(BaseConfig):
    user_pool_id = 'us-west-2_LQnstneoZ'
    app_id = '2seju0a0p55hmdajb61ftm4edc'
    data_endpoint = 'https://22boctowkfbuzaidvbvwjxfnai.appsync-api.us-west-2.amazonaws.com/graphql'
    rest_endpoint = 'https://3b71dp5mn2.execute-api.us-west-2.amazonaws.com/prd'
    region = 'us-west-2'
    resources_bucket = 'pubweb-resources-prd'
    references_bucket = 'pubweb-resources'
    base_url = 'https://pubweb.cloud'


if os.environ.get('ENV', '').upper() == 'DEV':
    config = DevelopmentConfig()
else:
    config = ProductionConfig()
