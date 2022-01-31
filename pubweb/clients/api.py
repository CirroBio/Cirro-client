from typing import Dict

import requests
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from graphql import DocumentNode, OperationDefinitionNode

from pubweb import config
from pubweb.auth.base import AuthInfo

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


def _build_gql_client(auth_info: AuthInfo, endpoint: str):
    transport = RequestsHTTPTransport(url=endpoint, headers=HEADERS, auth=auth_info.get_request_auth())
    return Client(transport=transport, fetch_schema_from_transport=True)


class ApiClient:
    def __init__(self, auth_info: AuthInfo):
        self.rest_endpoint = config.rest_endpoint
        self.auth_info = auth_info
        self.gql_client = _build_gql_client(auth_info, config.data_endpoint)

    def post(self, path, data=None):
        url = f'{self.rest_endpoint}/{path}'
        return requests.post(url, json=data, headers=HEADERS, auth=self.auth_info.get_request_auth())

    def get(self, path, query_params=None):
        url = f'{self.rest_endpoint}/{path}'
        return requests.get(url, params=query_params, headers=HEADERS, auth=self.auth_info.get_request_auth())

    def query(self, query: DocumentNode, variables=None) -> Dict:
        return self.gql_client.execute(query, variable_values=variables)
