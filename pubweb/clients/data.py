from functools import lru_cache
from typing import List

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from requests.auth import AuthBase

from pubweb import config


def _filter_deleted(items: List) -> List:
    return list(filter(lambda item: not item.get('_deleted', False), items))


def get_id_from_name(items, name_or_id) -> str:
    matched = next((p for p in items if p['id'] == name_or_id), None)
    if matched:
        return matched['id']
    return next(p for p in items if p['name'] == name_or_id)['id']


def _build_client(auth_info: AuthBase, endpoint: str):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    transport = RequestsHTTPTransport(url=endpoint, headers=headers, auth=auth_info)
    return Client(transport=transport, fetch_schema_from_transport=True)


class DataClient:
    def __init__(self, auth_info: AuthBase):
        self.client = _build_client(auth_info, config.data_endpoint)

    def get_project_id(self, name_or_id):
        return get_id_from_name(self.get_projects_list(), name_or_id)

    def get_process_id(self, name_or_id):
        return get_id_from_name(self.get_ingest_processes(), name_or_id)

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
    def get_datasets_list(self, project_id) -> List:
        query = gql('''
          query DatasetsByProject(
            $project: ID!
            $sortDirection: ModelSortDirection
            $filter: ModelDatasetFilterInput
            $limit: Int
            $nextToken: String
          ) {
            datasetsByProject(
              project: $project
              sortDirection: $sortDirection
              filter: $filter
              limit: $limit
              nextToken: $nextToken
            ) {
              items {
                id
                status
                name
                desc
                sourceDatasets
                infoJson
                process
                createdAt
                updatedAt
                _deleted
              }
              nextToken
              startedAt
            }
          }
        ''')
        variables = {
            'project': project_id,
            'filter': {
                'status': {
                    'eq': 'COMPLETED'
                }
            }
        }
        resp = self.client.execute(query, variable_values=variables)['datasetsByProject']
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
            'executor': {'eq': 'INGEST'}
        }
        resp = self.client.execute(query, variable_values={'filter': item_filter})['listProcesses']
        return _filter_deleted(resp['items'])
