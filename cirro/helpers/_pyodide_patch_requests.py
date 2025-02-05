from cirro.sdk.file import DataPortalFile
import requests


def _get(self: DataPortalFile):
    # Load lazily -- must be installed with the pyodide extras
    try:
        from requests_aws4auth import AWS4Auth # noqa
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Could not load requests_aws4auth -- make sure to install cirro[pyodide]")

    # Get the access context and credentials
    access_context = self._file.access_context
    creds = (
        self
        ._client
        ._file_service
        .get_access_credentials(access_context)
    )

    # Construct the URL endpoint to the file
    endpoint = "/".join([
        f"https://{access_context.bucket}.s3.{creds.region}.amazonaws.com",
        access_context.prefix,
        self._file.relative_path
    ])

    # Set up the authorization
    auth = AWS4Auth(
        creds.access_key_id,
        creds.secret_access_key,
        creds.region,
        's3',
        session_token=creds.session_token,
    )

    # Make the request
    response = requests.get(endpoint, auth=auth)

    # Raise an error if the exit code is not 400
    response.raise_for_status()

    # Return the contents of the response
    return response.content


def pyodide_patch_requests():
    DataPortalFile._get = _get
