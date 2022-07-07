import json
from datetime import timezone, datetime
from typing import Optional, Union, List, Callable, TypeVar

from pubweb.models.auth import Creds

T = TypeVar("T")


def parse_json_date(json_date: str) -> Optional[datetime]:
    if not json_date:
        return None
    local_zone = datetime.now(timezone.utc).astimezone().tzinfo
    try:
        parsed = datetime.strptime(json_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        # AWS Format
        parsed = datetime.strptime(json_date, "%Y-%m-%dT%H:%M:%S+00:00")

    return parsed\
        .replace(tzinfo=timezone.utc)\
        .astimezone(local_zone)


def safe_load_json(json_str: Optional[str]):
    if json_str is not None:
        return json.loads(json_str)
    else:
        return {}


def format_date(date: Union[str, datetime]) -> str:
    if isinstance(date, str):
        date = parse_json_date(date)
    return date.strftime('%m/%d/%Y, %H:%M:%S')


def print_credentials(creds: Creds):
    print(f'AWS_ACCESS_KEY_ID: {creds["AccessKeyId"]}')
    print(f'AWS_SECRET_ACCESS_KEY: {creds["SecretAccessKey"]}')
    print(f'AWS_SESSION_TOKEN: {creds["SessionToken"]}')
    if creds['Expiration']:
        print()
        print(f'These credentials expire at {format_date(creds["Expiration"])}')


def find_first(items: List[T], query: Callable[[T], bool]) -> Optional[T]:
    return next((item for item in items if query(item)), None)
