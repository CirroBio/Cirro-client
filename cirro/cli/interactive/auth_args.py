from typing import Tuple, Dict

from cirro.api.auth import ClientAuth, UsernameAndPasswordAuth, IAMAuth
from cirro.cli.interactive.utils import ask, ask_yes_no


def gather_auth_config() -> Tuple[str, Dict]:
    auth_method_config = {
        'enable_cache': ask_yes_no("Would you like to cache your login?")
    }

    return 'ClientAuth', auth_method_config
