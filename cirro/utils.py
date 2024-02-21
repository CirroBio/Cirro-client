import json
import math
from datetime import timezone, datetime
from typing import Optional, Union

from cirro_api_client.v1.models import AWSCredentials


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
    if json_str is None:
        return {}

    return json.loads(json_str)


def format_date(date: Union[str, datetime]) -> str:
    if isinstance(date, str):
        date = parse_json_date(date)
    return date.strftime('%m/%d/%Y, %H:%M:%S')


def print_credentials(creds: AWSCredentials):
    print(f'AWS_ACCESS_KEY_ID={creds.access_key_id}')
    print(f'AWS_SECRET_ACCESS_KEY={creds.secret_access_key}')
    print(f'AWS_SESSION_TOKEN={creds.session_token}')
    if creds.expiration:
        print()
        print(f'These credentials expire at {format_date(creds.expiration)}')


def convert_size(size: int):
    if size == 0:
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size/p, 2)
    return '%.2f %s' % (s, size_name[i])
