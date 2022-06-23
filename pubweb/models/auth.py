from typing import TypedDict


class Creds(TypedDict):
    AccessKeyId: str
    Expiration: str
    SecretAccessKey: str
    SessionToken: str


def print_credentials(creds: Creds):
    print(f'AWS_ACCESS_KEY_ID:{creds["AccessKeyId"]}')
    print(f'AWS_SECRET_ACCESS_KEY:{creds["SecretAccessKey"]}')
    print(f'AWS_SESSION_TOKEN:{creds["SessionToken"]}')
