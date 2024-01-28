from cirro.models.reference import Reference
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset


class DataPortalReference(DataPortalAsset):
    """
    Reference data is organized by project, categorized by type.
    """
    def __init__(self, ref: Reference):
        self.data = ref

    @property
    def name(self):
        return self.data.name

    @property
    def type(self):
        return self.data.type

    @property
    def files(self):
        return self.data.files

    def __str__(self):
        return self.name


class DataPortalReferences(DataPortalAssets[DataPortalReference]):
    """Collection of DataPortalReference objects."""
    asset_name = "reference"

    def get_by_id(self, _id: str) -> DataPortalReference:
        raise NotImplementedError("Filtering by ID is not supported, use get_by_name")
