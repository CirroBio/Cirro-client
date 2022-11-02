from typing import TypedDict, Optional


class Creds(TypedDict):
    AccessKeyId: str
    SecretAccessKey: str
    SessionToken: Optional[str]
    Expiration: Optional[str]
