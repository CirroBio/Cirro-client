from pubweb.api.models.reference import Reference
from pubweb.sdk.asset import DataPortalAssets, DataPortalAsset


class DataPortalReference(DataPortalAsset):
    """
    Reference data is organized by project, categorized by type.
    """
    name = None

    def __init__(self, ref: Reference):
        self.name = ref.name
        self._access_context = ref.access_context
        self.relative_path = ref.relative_path
        self.absolute_path = f'{self._access_context.domain}/{self.relative_path.strip("/")}'

    def __str__(self):
        return self.name


class DataPortalReferences(DataPortalAssets[DataPortalReference]):
    """Collection of DataPortalReference objects."""
    asset_name = "reference"

    def get_by_id(self, _id: str) -> DataPortalReference:
        raise NotImplementedError("Filtering by ID is not supported, use get_by_name")
