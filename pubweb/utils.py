from datetime import timezone, datetime

from pubweb.models.auth import Creds


def parse_json_date(json_date: str) -> datetime:
    local_zone = datetime.now(timezone.utc).astimezone().tzinfo
    return datetime.strptime(json_date, "%Y-%m-%dT%H:%M:%S.%fZ")\
        .replace(tzinfo=timezone.utc)\
        .astimezone(local_zone)


def format_date(json_date: str) -> str:
    return parse_json_date(json_date).strftime('%m/%d/%Y, %H:%M:%S')


def print_credentials(creds: Creds):
    print(f'AWS_ACCESS_KEY_ID: {creds["AccessKeyId"]}')
    print(f'AWS_SECRET_ACCESS_KEY: {creds["SecretAccessKey"]}')
    print(f'AWS_SESSION_TOKEN: {creds["SessionToken"]}')
