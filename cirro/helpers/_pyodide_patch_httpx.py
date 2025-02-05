import httpx
import requests
from httpx import Headers, Request, Response, Auth
from httpx._client import Client, logger
from requests.auth import AuthBase


class HttpxToRequestsAuth(AuthBase):
    def __init__(self, httpx_auth):
        self.httpx_auth: Auth = httpx_auth

    def __call__(self, request: Request):

        # Create a mock HTTPX request
        httpx_request = httpx.Request(
            method=request.method,
            url=request.url,
            headers=request.headers
        )

        # Apply the httpx authentication
        if self.httpx_auth:
            self.httpx_auth.auth_flow(httpx_request)

        # Copy back modified headers to the requests request
        request.headers.update(httpx_request.headers)

        return request


def _send_single_request(self: Client, request: Request) -> Response:
    auth_patched = HttpxToRequestsAuth(self.auth)

    resp = requests.request(
        method=request.method,
        url=request.url,
        headers=request.headers,
        data=request.content,
        auth=auth_patched,

    )

    if "content-encoding" in resp.headers:
        del resp.headers["content-encoding"]

    response = Response(
        status_code=resp.status_code,
        headers=Headers(resp.headers),
        content=resp.content,
        request=httpx.Request(method=resp.request.method, url=str(resp.url)),
    )

    logger.info(
        'HTTP Request: %s %s "%s %d %s"',
        request.method,
        request.url,
        response.http_version,
        response.status_code,
        response.reason_phrase,
    )

    return response


def pyodide_patch_httpx():
    Client._send_single_request = _send_single_request
