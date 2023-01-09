import platform
from typing import Dict

import pkg_resources
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from cirro.api.auth.base import AuthInfo
from cirro.api.auth.iam import IAMAuth

try:
    sdk_version = pkg_resources.get_distribution("cirro").version
except (pkg_resources.RequirementParseError, TypeError):
    sdk_version = "Unknown"
python_version = platform.python_version()
headers = {
    'User-Agent': f'Cirro SDK {sdk_version} (Python {python_version})',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


def _build_gql_client(auth_info: AuthInfo, endpoint: str):
    transport = RequestsHTTPTransport(url=endpoint, headers=headers, auth=auth_info.get_request_auth())
    return Client(transport=transport, fetch_schema_from_transport=False)


class ApiClient:
    def __init__(self, auth_info: AuthInfo, data_endpoint: str):
        self._auth_info = auth_info
        self._gql_client = _build_gql_client(auth_info, data_endpoint)

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
