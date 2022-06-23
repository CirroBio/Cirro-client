from typing import TypedDict, Optional


class Creds(TypedDict):
    AccessKeyId: str
    SecretAccessKey: str
    SessionToken: Optional[str]
    Expiration: Optional[str]


def print_credentials(creds: Creds):
    print(f'AWS_ACCESS_KEY_ID:{creds["AccessKeyId"]}')
    print(f'AWS_SECRET_ACCESS_KEY:{creds["SecretAccessKey"]}')
    print(f'AWS_SESSION_TOKEN:{creds["SessionToken"]}')
