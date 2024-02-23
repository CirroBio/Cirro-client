from typing import List, Optional

from cirro_api_client.v1.api.projects import get_projects, create_project, get_project, set_user_project_role, \
    update_project, update_project_tags, get_project_users
from cirro_api_client.v1.models import ProjectRequest, SetUserProjectRoleRequest, Tag, ProjectRole, ProjectDetail, \
    CreateResponse, ProjectUser

from cirro.services.base import BaseService


class ProjectService(BaseService):
    """
    Service for interacting with the Project endpoints
    """
    def list(self):
        """
        Retrieve a list of projects
        """
        return get_projects.sync(client=self._api_client)

    def get(self, project_id: str) -> ProjectDetail:
        """
        Get detailed project information

        Args:
            project_id (str): Project ID
        """
        return get_project.sync(project_id=project_id, client=self._api_client)

    def create(self, request: ProjectRequest) -> CreateResponse:
        """
        Create a project

        Args:
            request (`cirro_api_client.v1.models.ProjectRequest`): Detailed information about the project to create

        ```python
        from cirro_api_client.v1.models import ProjectRequest, ProjectSettings, Contact
        from cirro.cirro_client import CirroApi

        cirro = CirroApi()
        request = ProjectRequest(
            name="New Project Name",
            description="Description of new project",
            billing_account_id="billing-account-id",
            settings=ProjectSettings(
                budget_period="MONTHLY",
                max_spot_vcpu=300,
                budget_amount=1000
            ),
            contacts=[
                Contact(
                    name="Contact Name",
                    organization="Contact Organization",
                    email="contact@email.com",
                    phone="987-654-3210"
                )
            ],
        )
        cirro.projects.create(request)
        ```
        """
        return create_project.sync(client=self._api_client, body=request)

    def update(self, project_id: str, request: ProjectRequest) -> ProjectDetail:
        """
        Updates a project

        Args:
            project_id (str): ID of project to update
            request (`cirro_api_client.v1.models.ProjectRequest`): New details for the project
        """
        return update_project.sync(project_id=project_id, body=request, client=self._api_client)

    def update_tags(self, project_id: str, tags: List[Tag]):
        """
        Sets tags on a project

        Args:
            project_id (str): Project ID
            tags (List[Tag]): List of tags to apply
        """
        update_project_tags.sync_detailed(project_id=project_id, body=tags, client=self._api_client)

    def get_users(self, project_id: str) -> Optional[List[ProjectUser]]:
        """
        Gets users who have access to the project

        Args:
            project_id (str): Project ID
        """
        return get_project_users.sync(project_id=project_id, client=self._api_client)

    def set_user_role(self, project_id: str, username: str, role: ProjectRole, supress_notification=False):
        """
        Sets a user's role within a project.

        Set to `ProjectRole.NONE` if removing the user from a project.

        Args:
            project_id (str): Project ID
            username (str): Username
            role (`cirro_api_client.v1.models.ProjectRole`): New role to apply
            supress_notification (bool):
        """
        request_body = SetUserProjectRoleRequest(
            username=username,
            role=role,
            supress_notification=supress_notification
        )
        set_user_project_role.sync_detailed(project_id=project_id, body=request_body, client=self._api_client)
