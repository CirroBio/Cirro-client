from typing import List

from attrs import define
from cirro_api_client.v1.models import ArtifactType

from cirro.models.file import File


@define
class Artifact:
    """
    An artifact is a file that is a secondary file associated with the dataset.
    This could be a workflow execution report, a log file, or any other file generated as a result of an analysis.
    """
    artifact_type: ArtifactType
    file: File


@define
class DatasetAssets:
    """
    Container for assets associated with a dataset (files, artifacts, etc.)
    """
    files: List[File]
    artifacts: List[Artifact]
