import os
from typing import Tuple

from pubweb.cli.interactive.utils import ask


def gather_login() -> Tuple[str, str]:
    username = ask('text', 'Username',
                   default=os.environ.get('PW_USERNAME') or '')
    password = ask('text', 'Password')
    return username, password
