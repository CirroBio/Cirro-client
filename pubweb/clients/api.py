from typing import Dict

from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from graphql import DocumentNode

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
        self._gql_client = _build_gql_client(auth_info, config.data_endpoint)

    def query(self, query: DocumentNode, variables=None) -> Dict:
        return self._gql_client.execute(query, variable_values=variables)
