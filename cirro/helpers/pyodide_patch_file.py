import requests

from cirro.models.file import FileAccessContext
from cirro.services import FileService


def _get_file_from_path(self: FileService, access_context: FileAccessContext, file_path: str):
    # Load lazily -- must be installed with the pyodide extras
    try:
        from requests_aws4auth import AWS4Auth # noqa
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Could not load requests_aws4auth -- make sure to install cirro[pyodide]")

    creds = self.get_access_credentials(access_context)

    # Construct the URL endpoint to the file
    endpoint = "/".join([
        f"https://{access_context.bucket}.s3.{creds.region}.amazonaws.com",
        access_context.prefix,
        file_path
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
    response = requests.get(endpoint, auth=auth, stream=True)

    # Raise an error if the exit code is not 400
    response.raise_for_status()

    # Read the content of the response and decode it
    content = response.raw.read(decode_content=True)

    # Return the contents of the response
    return content


def pyodide_patch_file():
    """
    Patch the FileService to use requests to get files from S3,
     rather than S3Client (boto3)
    """
    FileService.get_file_from_path = _get_file_from_path
