from cirro.api.auth.iam import IAMAuth
from cirro.api.clients.portal import DataPortalClient
from cirro.api.models.exceptions import DataPortalModelException
from cirro.api.models.process import Executor
from cirro.api.models.project import Project
from cirro.sdk.asset import DataPortalAsset
from cirro.sdk.process import DataPortalProcess, DataPortalProcesses
from cirro.sdk.project import DataPortalProject, DataPortalProjects
from cirro.sdk.reference_type import DataPortalReferenceType, DataPortalReferenceTypes


class DataPortal(DataPortalAsset):
    """
    Helper functions for exploring the Projects, Datasets, Samples, and Files
    available in the Data Portal.
    """

    def __init__(self, client: DataPortalClient = None):
        """Set up the DataPortal object, establishing an authenticated connection."""

        # If this is a headless execution environment
        if self._in_headless:

            # Set up the client using the IAM role
            self._client = DataPortalClient(auth_info=IAMAuth.load_current())

        # If this is not a notebook environment
        else:

            # If the client object was provided
            if client is not None:
                self._client = client

            # Set up default client if not provided
            else:
                self._client = DataPortalClient()

    def list_projects(self) -> DataPortalProjects:
        """List all of the projects available in the Data Portal."""

        # In the notebook environment, only the $CIRRO_NB_PROJECT project is available
        if self._in_headless:

            # Read the project data
            proj = self._headless_project_data()

            # Return a list with only that single project in it
            return DataPortalProjects([
                DataPortalProject(
                    Project(
                        id=proj['id'],
                        name=proj['name'],
                        description=proj['description']
                    ),
                    self._client
                )
            ])

        else:

            # Otherwise, get the list of projects from the API
            return DataPortalProjects(
                [
                    DataPortalProject(proj, self._client)
                    for proj in self._client.project.list()
                ]
            )

    def get_project_by_name(self, name: str = None) -> DataPortalProject:
        """Return the project with the specified name."""

        return self.list_projects().get_by_name(name)

    def get_project_by_id(self, _id: str = None) -> DataPortalProject:
        """Return the project with the specified id."""

        return self.list_projects().get_by_id(_id)

    def list_processes(self, ingest=False) -> DataPortalProcesses:
        """
        List all of the processes available in the Data Portal.
        By default, only list non-ingest processes (those which can be run on existing datasets).
        To list the processes which can be used to upload datasets, use ingest = True.
        Note: Processes are not available while running in headless execution mode.
        """

        if self._in_headless:
            raise DataPortalModelException("Cannot access processes")

        return DataPortalProcesses(
            [
                DataPortalProcess(p, self._client)
                for p in self._client.process.list()
                if (p.executor == Executor.INGEST) == ingest
            ]
        )

    def get_process_by_name(self, name: str, ingest=False) -> DataPortalProcess:
        """Return the process with the specified name."""

        return self.list_processes(ingest=ingest).get_by_name(name)

    def get_process_by_id(self, _id: str, ingest=False) -> DataPortalProcess:
        """Return the process with the specified id."""

        return self.list_processes(ingest=ingest).get_by_id(_id)

    def list_reference_types(self) -> DataPortalReferenceTypes:
        """
        Return the list of all available reference types.
        Note: References are not available while running in headless execution mode.
        """

        if self._in_headless:
            raise DataPortalModelException("Cannot access references")

        return DataPortalReferenceTypes(
            [
                DataPortalReferenceType(ref)
                for ref in self._client.common.get_references_types()
            ]
        )
