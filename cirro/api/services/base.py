from abc import ABC
from typing import Dict

from cirro.api.clients import ApiClient
from cirro.api.config import AppConfig


def fetch_all_items(client: ApiClient, query: str, input_variables: Dict, batch_size=10000, max_items=None):
    """
    Fetches all items from a paginated graphql api
    """
    next_token = None
    items = []
    while True:
        variables = {
            'nextToken': next_token,
            'limit': batch_size,
            **input_variables
        }
        resp = client.query(query, variables)
        query_name = next(iter(resp.keys()))
        items.extend(resp[query_name]['items'])

        next_token = resp[query_name]['nextToken']
        if not next_token:
            return items

        if max_items and len(items) >= max_items:
            return items


class BaseService(ABC):
    _api_client: ApiClient
    _configuration: AppConfig

    def __init__(self, api_client: ApiClient, configuration: AppConfig):
        self._api_client = api_client
        self._configuration = configuration
