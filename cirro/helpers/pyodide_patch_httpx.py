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

    # Send the request using requests
    resp = requests.request(
        method=request.method,
        url=request.url,
        headers=request.headers,
        data=request.content,
        auth=auth_patched,
        stream=True
    )

    # If the response is not successful, raise an HTTPError
    if not resp.ok:
        raise httpx.HTTPStatusError(
            f"HTTP request failed with status code {resp.status_code}",
            request=request,
            response=resp
        )

    # Read the content of the response and decode it
    content = resp.raw.read(decode_content=True)

    # Remove content-encoding header to prevent httpx from trying to decode the content
    # since requests already decodes the content
    if "content-encoding" in resp.headers:
        del resp.headers["content-encoding"]

    # Transform the requests response to the httpx response
    response = Response(
        status_code=resp.status_code,
        headers=Headers(resp.headers),
        content=content,
        request=httpx.Request(method=resp.request.method, url=str(resp.url)),
    )

    logger.debug(
        'HTTP Request: %s %s "%s %d %s"',
        request.method,
        request.url,
        response.http_version,
        response.status_code,
        response.reason_phrase,
    )

    return response


def pyodide_patch_httpx():
    """
    Patch the httpx.Client to use requests to send requests
    """
    Client._send_single_request = _send_single_request
