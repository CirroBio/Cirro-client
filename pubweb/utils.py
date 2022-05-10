from datetime import timezone, datetime


def parse_json_date(json_date: str) -> datetime:
    local_zone = datetime.now(timezone.utc).astimezone().tzinfo
    return datetime.strptime(json_date, "%Y-%m-%dT%H:%M:%S.%fZ")\
        .replace(tzinfo=timezone.utc)\
        .astimezone(local_zone)


def format_date(json_date: str) -> str:
    return parse_json_date(json_date).strftime('%m/%d/%Y, %H:%M:%S')
