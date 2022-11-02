from pubweb.api.models.reference import ReferenceType
from pubweb.sdk.asset import DataPortalAssets


class DataPortalReferenceType:
    """
    Reference data is organized by project, categorized by type.
    """

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


class DataPortalReferenceTypes(DataPortalAssets):
    asset_name = "reference type"
    asset_class = DataPortalReferenceType
