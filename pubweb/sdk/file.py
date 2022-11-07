import gzip
from io import BytesIO, StringIO

import pandas as pd

from pubweb.api.clients.portal import DataPortalClient
from pubweb.api.models.file import File
from pubweb.sdk.asset import DataPortalAssets, DataPortalAsset
from pubweb.sdk.exceptions import DataPortalInputError


class DataPortalFile(DataPortalAsset):
    """
    Datasets are made up of a collection of File objects in the Data Portal.
    """
    name = None

    def __init__(self, file: File, client: DataPortalClient):

        # Note that the 'name' and 'id' attributes are set to the relative path
        # The purpose of this is to support the DataPortalAssets class functions
        self.name = file.relative_path
        self.id = file.relative_path
        self.absolute_path = file.absolute_path

        # Inherit all of the other attributes
        self.relative_path = file.relative_path
        self.size = file.size
        self._access_context = file.access_context
        self._client = client

        # Attach the file object
        self.file = file

    def __str__(self):
        return f"{self.relative_path} ({self.size} bytes)"

    def _get(self) -> bytes:
        """Internal method to call client.file.get_file"""

        return self._client.file.get_file(self.file)

    def read_csv(self, compression='infer', encoding='utf-8', **kwargs):
        """
        Parse the file as a Pandas DataFrame.

        The default field separator is a comma (for CSV), use sep='\\t' for TSV.

        File compression is inferred from the extension, but can be set
        explicitly with the compression= flag.

        All other keyword arguments are passed to pandas.read_csv
        https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
        """

        if compression == 'infer':
            # If the file appears to be compressed
            if self.relative_path.endswith('.gz'):
                compression = dict(method='gzip')
            elif self.relative_path.endswith('.bz2'):
                compression = dict(method='bz2')
            elif self.relative_path.endswith('.xz'):
                compression = dict(method='zstd')
            elif self.relative_path.endswith('.zst'):
                compression = dict(method='zstd')
            else:
                compression = None

        if compression is not None:
            handle = BytesIO(self._get())
        else:
            handle = StringIO(self._get().decode(encoding))

        df = pd.read_csv(
            handle,
            compression=compression,
            encoding=encoding,
            **kwargs
        )
        handle.close()
        return df

    def readlines(self, encoding='utf-8', compression=None):
        """Read the file contents as a list of lines."""

        return self.read(
            encoding=encoding,
            compression=compression
        ).splitlines()

    def read(self, encoding='utf-8', compression=None) -> str:
        """Read the file contents as text."""

        # Get the raw file contents
        cont = self._get()

        # If the file is uncompressed
        if compression is None:
            return cont.decode(encoding)
        # If the file is compressed
        else:

            # Only gzip-compression is supported currently
            if compression != "gzip":
                raise DataPortalInputError("compression may be 'gzip' or None")

            with gzip.open(
                BytesIO(
                    cont
                ),
                'rt',
                encoding=encoding
            ) as handle:
                return handle.read()

    def download(self, download_location: str = None):
        """Download the file to a local directory."""

        if download_location is None:
            raise DataPortalInputError("Must provide download location")

        self._client.file.download_files(
            self.file.access_context,
            download_location,
            [self.relative_path]
        )


class DataPortalFiles(DataPortalAssets[DataPortalFile]):
    """Collection of DataPortalFile objects."""
    asset_name = "file"

    def download(self, download_location: str = None) -> None:
        """Download the collection of files to a local directory."""

        for f in self:
            f.download(download_location)
