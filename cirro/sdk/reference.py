from cirro_api_client.v1.models import Reference

from cirro.cirro_client import Cirro
from cirro.models.file import File
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset
from cirro.sdk.file import DataPortalFile


class DataPortalReference(DataPortalAsset):
    """
    Reference data is organized by project, categorized by type.
    """
    def __init__(self, ref: Reference, project_id: str, client: Cirro):
        self.data = ref
        self.files = [
            DataPortalFile(File.from_file_entry(f, project_id), client) for f in ref.files
        ]

    @property
    def name(self):
        return self.data.name

    @property
    def type(self):
        return self.data.type

    def __str__(self):
        return self.name


class DataPortalReferences(DataPortalAssets[DataPortalReference]):
    """Collection of DataPortalReference objects."""
    asset_name = "reference"

    def get_by_id(self, _id: str) -> DataPortalReference:
        raise NotImplementedError("Filtering by ID is not supported, use get_by_name")
