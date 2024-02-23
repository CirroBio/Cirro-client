from cirro_api_client.v1.models import Executor

from cirro.cirro_client import CirroAPI
from cirro.sdk.process import DataPortalProcess, DataPortalProcesses
from cirro.sdk.project import DataPortalProject, DataPortalProjects
from cirro.sdk.dataset import DataPortalDataset
from cirro.sdk.reference_type import DataPortalReferenceType, DataPortalReferenceTypes
from cirro.sdk.exceptions import DataPortalAssetNotFound


class DataPortal:
    """
    Helper functions for exploring the Projects, Datasets, Samples, and Files
    available in the Data Portal.
    """

    def __init__(self, client: CirroAPI = None):
        """Set up the DataPortal object, establishing an authenticated connection."""

        if client is not None:
            self._client = client

        # Set up default client if not provided
        else:
            self._client = CirroAPI()

    def list_projects(self) -> DataPortalProjects:
        """List all the projects available in the Data Portal."""

        return DataPortalProjects(
            [
                DataPortalProject(proj, self._client)
                for proj in self._client.projects.list()
            ]
        )

    def get_project_by_name(self, name: str = None) -> DataPortalProject:
        """Return the project with the specified name."""

        return self.list_projects().get_by_name(name)

    def get_project_by_id(self, _id: str = None) -> DataPortalProject:
        """Return the project with the specified id."""

        return self.list_projects().get_by_id(_id)

    def get_dataset(self, project: str = None, dataset: str = None) -> DataPortalDataset:
        """
        Return a dataset identified by ID or name.

        Args:
            project (str): ID or name of project
            dataset (str): ID or name of dataset

        Returns:
            `cirro.sdk.dataset.DataPortalDataset`

            ```
            from cirro import DataPortal()
            portal = DataPortal()
            dataset = portal.get_dataset(
                project="id-or-name-of-project",
                dataset="id-or-name-of-dataset"
            )
            ```
        """
        try:
            project: DataPortalProject = self.get_project_by_id(project)
        except DataPortalAssetNotFound:
            project: DataPortalProject = self.get_project_by_name(project)

        try:
            return project.get_dataset_by_id(dataset)
        except DataPortalAssetNotFound:
            return project.get_dataset_by_name(dataset)

    def list_processes(self, ingest=False) -> DataPortalProcesses:
        """
        List all the processes available in the Data Portal.
        By default, only list non-ingest processes (those which can be run on existing datasets).
        To list the processes which can be used to upload datasets, use ingest = True.

        Args:
            ingest (bool): If True, only list those processes which can be used to ingest datasets directly

        Returns:
            `cirro.sdk.process.DataPortalProcesses`
        """

        return DataPortalProcesses(
            [
                DataPortalProcess(p, self._client)
                for p in self._client.processes.list()
                if not ingest or p.executor == Executor.INGEST
            ]
        )

    def get_process_by_name(self, name: str, ingest=False) -> DataPortalProcess:
        """
        Return the process with the specified name.

        Args:
            name (str): Name of process

        Returns:
            `cirro.sdk.process.DataPortalProcess`
        """

        return self.list_processes(ingest=ingest).get_by_name(name)

    def get_process_by_id(self, id: str, ingest=False) -> DataPortalProcess:
        """
        Return the process with the specified id

        Args:
            id (str): ID of process

        Returns:
            `cirro.sdk.process.DataPortalProcess`
        """

        return self.list_processes(ingest=ingest).get_by_id(id)

    def list_reference_types(self) -> DataPortalReferenceTypes:
        """
        Return the list of all available reference types

        Returns:
            `cirro.sdk.reference_type.DataPortalReferenceTypes`
        """

        return DataPortalReferenceTypes(
            [
                DataPortalReferenceType(ref)
                for ref in self._client.references.get_types()
            ]
        )
