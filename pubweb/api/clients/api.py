from typing import Dict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from pubweb.api.auth.base import AuthInfo
from pubweb.api.auth.iam import IAMAuth
from pubweb.api.config import config

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


def _build_gql_client(auth_info: AuthInfo, endpoint: str):
    transport = RequestsHTTPTransport(url=endpoint, headers=HEADERS, auth=auth_info.get_request_auth())
    return Client(transport=transport, fetch_schema_from_transport=False)


class ApiClient:
    def __init__(self, auth_info: AuthInfo):
        self._auth_info = auth_info
        self._gql_client = _build_gql_client(auth_info, config.data_endpoint)

    def query(self, query: str, variables=None) -> Dict:
        return self._gql_client.execute(gql(query), variable_values=variables)

    @property
    def has_iam_creds(self) -> bool:
        return isinstance(self._auth_info, IAMAuth)

    @property
    def current_user(self) -> str:
        return self._auth_info.get_current_user()

    def get_iam_creds(self):
        if self.has_iam_creds:
            return self._auth_info.creds
