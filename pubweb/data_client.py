from functools import lru_cache
from typing import List

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from requests.auth import AuthBase

PUB_WEB_ENDPOINT = 'https://22boctowkfbuzaidvbvwjxfnai.appsync-api.us-west-2.amazonaws.com/graphql'
REGION = 'us-west-2'
DELETED_FILTER = {
    '_deleted': False
}


def _filter_deleted(items: List) -> List:
    return list(filter(lambda item: not item.get('_deleted', False), items))


def _build_client(auth_info: AuthBase, endpoint: str):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    transport = RequestsHTTPTransport(url=endpoint, headers=headers, auth=auth_info)
    return Client(transport=transport, fetch_schema_from_transport=True)


class DataClient:
    def __init__(self, auth_info: AuthBase, endpoint=PUB_WEB_ENDPOINT):
        self.client = _build_client(auth_info, endpoint)

    @lru_cache
    def get_projects_list(self) -> List:
        query = gql('''
          query ListProjects(
            $filter: ModelProjectFilterInput
            $limit: Int
            $nextToken: String
          ) {
            listProjects(filter: $filter, limit: $limit, nextToken: $nextToken) {
              items {
                id
                name
                desc
                _deleted
              }
            }
          }
        ''')

        resp = self.client.execute(query)['listProjects']
        return _filter_deleted(resp['items'])

    @lru_cache
    def get_ingest_processes(self) -> List:
        query = gql('''
          query ListProcesses(
            $filter: ModelProcessFilterInput
            $limit: Int
            $nextToken: String
          ) {
            listProcesses(filter: $filter, limit: $limit, nextToken: $nextToken) {
              items {
                id
                name
                desc
                _deleted
              }
            }
          }
        ''')
        item_filter = {
            'executor': {'eq': 'INGEST'},
            '_deleted': {'eq': False}
        }
        resp = self.client.execute(query, variable_values={'filter': item_filter})['listProcesses']
        return _filter_deleted(resp['items'])
