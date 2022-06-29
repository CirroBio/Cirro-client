import os

from pubweb.cli.interactive.utils import prompt_wrapper


def gather_login():
    answers = prompt_wrapper([
        {
            'type': 'input',
            'name': 'username',
            'message': 'Username',
            'default': os.environ.get('PW_USERNAME') or ''
        },
        {
            'type': 'password',
            'name': 'password',
            'message': 'Password'
        }
    ])
    return answers['username'], answers['password']
