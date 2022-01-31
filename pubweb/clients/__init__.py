from pubweb.clients.auth import CognitoAuthInfo
from pubweb.clients.data import DataClient
from pubweb.clients.rest import RestClient


def create_clients(username, password):
    auth_info = CognitoAuthInfo(username, password)
    data_client = DataClient(auth_info.get_request_auth())
    rest_client = RestClient(auth_info.get_request_auth())
    return data_client, rest_client
