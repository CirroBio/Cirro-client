from pubweb.api.models.reference import Reference
from pubweb.sdk.asset import DataPortalAssets


class DataPortalReference:
    """
    Reference data is organized by project, categorized by type.
    """

    def __init__(self, ref: Reference):
        self.name = ref.name
        self._access_context = ref.access_context
        self.relative_path = ref.relative_path
        self.absolute_path = f'{self._access_context.domain}/{self.relative_path.strip("/")}'

    def __str__(self):
        return self.name


class DataPortalReferences(DataPortalAssets):
    """Collection of DataPortalReference objects."""
    asset_name = "reference"
    asset_class = DataPortalReference
