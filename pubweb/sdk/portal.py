from pubweb.api.clients.portal import DataPortalClient
from pubweb.sdk.project import DataPortalProject, DataPortalProjects
from pubweb.sdk.process import DataPortalProcess, DataPortalProcesses
from pubweb.sdk.reference_type import DataPortalReferenceType, DataPortalReferenceTypes


class DataPortal:
    """
    Helper functions for exploring the projects, datasets, samples, and files
    available in the PubWeb Data Portal.
    """

    def __init__(self, client: DataPortalClient = None):
        """Set up the DataPortal object, establishing a connection with the PubWeb Data Portal."""

        # If the user provided their own client to get information from PubWeb
        if client is not None:

            # Attach it
            self._client = client

        # If the user did not provide their own client
        else:

            # Set up a client
            self._client = DataPortalClient()

    def list_projects(self) -> DataPortalProjects:
        """List all of the projects available in the Data Portal."""

        return DataPortalProjects(
            [
                DataPortalProject(proj, self._client)
                for proj in self._client.project.list()
            ]
        )

    def get_project_by_name(self, name: str = None) -> DataPortalProject:
        """Return the project with the specified name."""

        return self.list_projects().get_by_name(name)

    def get_project_by_id(self, id: str = None) -> DataPortalProject:
        """Return the project with the specified id."""

        return self.list_projects().get_by_id(id)

    def list_processes(self, ingest=False) -> DataPortalProcesses:
        """
        List all of the processes available in the Data Portal.
        By default, only list non-ingest processes (those which can be run on existing datasets).
        To list the processes which can be used to upload datasets, use ingest = True.
        """

        return DataPortalProcesses(
            [
                DataPortalProcess(p, self._client)
                for p in self._client.process.list()
                if (p.executor.name == "INGEST") == ingest
            ]
        )

    def get_process_by_name(self, name: str, ingest=False) -> DataPortalProcess:
        """Return the process with the specified name."""

        return self.list_processes(ingest=ingest).get_by_name(name)

    def get_process_by_id(self, id: str, ingest=False) -> DataPortalProcess:
        """Return the process with the specified id."""

        return self.list_processes(ingest=ingest).get_by_id(id)

    def list_reference_types(self):
        """Return the list of all available reference types."""

        return DataPortalReferenceTypes(
            [
                DataPortalReferenceType(ref)
                for ref in self._client.common.get_references_types()
            ]
        )