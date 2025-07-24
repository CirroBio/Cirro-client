from pathlib import Path
from typing import List, Optional

from cirro_api_client.v1.api.references import get_reference_types, get_references_for_project, \
    refresh_project_references
from cirro_api_client.v1.models import ReferenceType, Reference

from cirro.helpers.references import generate_reference_file_path_map
from cirro.models.file import PathLike, FileAccessContext
from cirro.services.file import FileEnabledService


class ReferenceService(FileEnabledService):
    """
    Service for interacting with the References endpoints
    """
    def get_types(self) -> Optional[List[ReferenceType]]:
        """
        List available reference types
        """
        return get_reference_types.sync(client=self._api_client)

    def get_type(self, reference_type_name: str) -> Optional[ReferenceType]:
        """
        Get a specific reference type by name

        Args:
            reference_type_name (str): Name of the reference type (e.g. "Reference Genome (FASTA)")
        """
        types = self.get_types()
        return next((t for t in types if t.name == reference_type_name), None)

    def get_for_project(self, project_id: str) -> Optional[List[Reference]]:
        """
        List available references for a given project
        """
        return get_references_for_project.sync(project_id=project_id, client=self._api_client)

    def upload_reference(self,
                         name: str,
                         reference_files: list[PathLike],
                         project_id: str,
                         ref_type: ReferenceType):
        """
        Upload a reference to a project

        Args:
            name (str): Name of the reference (e.g. "GRCh38")
                no spaces are allowed in the name
            reference_files (list[PathLike]): Path to the reference file to upload
            project_id (str): ID of the project to upload the reference to
            ref_type (ReferenceType): Type of the reference

        ```python
        from pathlib import Path

        from cirro import CirroApi

        cirro = CirroApi()

        crispr_library = cirro.references.get_type("CRISPR sgRNA Library")
        files = [
            Path("~/crispr_library.csv").expanduser()
        ]

        cirro.references.upload_reference(
            name="Library Name",
            project_id="project-id",
            ref_type=crispr_library,
            reference_files=files,
        )
        ```
        """
        # Validate name
        if ' ' in name:
            raise ValueError("Reference name cannot contain spaces")

        access_context = FileAccessContext.upload_reference(
            project_id=project_id,
            base_url=f's3://project-{project_id}/resources/data/references',
        )

        file_path_map = generate_reference_file_path_map(
            files=reference_files,
            name=name,
            ref_type=ref_type
        )

        self._file_service.upload_files(
            access_context=access_context,
            directory=Path('~').expanduser(),  # Full path expected in reference_files
            files=reference_files,
            file_path_map=file_path_map
        )

        refresh_project_references.sync_detailed(project_id=project_id,
                                                 client=self._api_client)
