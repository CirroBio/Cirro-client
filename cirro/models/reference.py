from typing import Optional, TypedDict


class ReferenceValidation(TypedDict):
    fileType: str
    saveAs: Optional[str]
    glob: Optional[str]
