import logging
from typing import List

from cirro_api_client.v1.api.projects import get_projects, create_project, get_project, set_user_project_role, \
    update_project, update_project_tags, get_project_users
from cirro_api_client.v1.models import ProjectRequest, SetUserProjectRoleRequest, Tag

from cirro.services.base import BaseService

logger = logging.getLogger()


class ProjectService(BaseService):
    def list(self):
        """
        Retrieve a list of projects
        """
        return get_projects.sync(client=self._api_client)

    def get(self, project_id: str):
        """
        Get detailed project information
        """
        return get_project.sync(project_id=project_id, client=self._api_client)

    def create(self, request: ProjectRequest):
        """
        Creates a project
        """
        return create_project.sync(client=self._api_client, body=request)

    def update(self, project_id: str, request: ProjectRequest):
        """
        Updates a project
        """
        return update_project.sync(project_id=project_id, body=request, client=self._api_client)

    def update_tags(self, project_id: str, tags: List[Tag]):
        """
        Sets tags on a project
        """
        update_project_tags.sync_detailed(project_id=project_id, body=tags, client=self._api_client)

    def get_users(self, project_id: str):
        """
        Gets users who have access to the project
        """
        return get_project_users.sync(project_id=project_id, client=self._api_client)

    def set_user_role(self, project_id: str, request: SetUserProjectRoleRequest):
        """
        Sets a user's role within a project
        """
        set_user_project_role.sync_detailed(project_id=project_id, body=request, client=self._api_client)
