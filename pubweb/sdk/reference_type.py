from pubweb.api.models.reference import ReferenceType
from pubweb.sdk.asset import DataPortalAssets, DataPortalAsset


class DataPortalReferenceType(DataPortalAsset):
    """
    Reference data is organized by project, categorized by type.
    """
    name = None

    def __init__(self, ref_type: ReferenceType):
        self.name = ref_type.name
        self.description = ref_type.description
        self.directory = ref_type.directory
        self.validation = ref_type.validation

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'description']
        ])


class DataPortalReferenceTypes(DataPortalAssets[DataPortalReferenceType]):
    """Collection of DataPortalReferenceType objects."""
    asset_name = "reference type"

    def get_by_id(self, _id: str) -> DataPortalReferenceType:
        raise NotImplementedError("Filtering by ID is not supported, use get_by_name")
