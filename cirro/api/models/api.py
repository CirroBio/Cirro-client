from typing import NamedTuple, Dict


class ApiQuery(NamedTuple):
    query: str
    variables: Dict
