import os

from PyInquirer import prompt


def gather_login():
    answers = prompt([
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
