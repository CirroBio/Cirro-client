from typing import TypedDict


class Creds(TypedDict):
    AccessKeyId: str
    Expiration: str
    SecretAccessKey: str
    SessionToken: str
