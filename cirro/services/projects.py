from typing import List, Optional

from cirro_api_client.v1.api.projects import get_projects, create_project, get_project, set_user_project_role, \
    update_project, update_project_tags, get_project_users, archive_project, unarchive_project
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

        Examples:
        ```python
        from cirro_api_client.v1.models import ProjectRequest, ProjectSettings, Contact, BudgetPeriod, CloudAccount, \
            CloudAccountType
        from cirro.cirro_client import CirroApi

        cirro = CirroApi()

        # Bring your own account projects are hosted by the user
        # You must provide the account details and VPC information
        # Please view the ProjectSettings model for more information on the attributes required
        byoa_project = ProjectRequest(
            name="New Project Name",
            description="Description of new project",
            billing_account_id="billing-account-id",
            settings=ProjectSettings(
                budget_period=BudgetPeriod.MONTHLY,
                budget_amount=1000,
                max_spot_vcpu=300,
                service_connections=[],
                retention_policy_days=7,
                vpc_id="vpc-000000000000",
                batch_subnets=["subnet-000000000000", "subnet-000000000001"],
                sagemaker_subnets=["subnet-000000000000", "subnet-000000000001"],
                kms_arn="arn:aws:kms:us-west-2:000000000000:key/00000000-0000-0000-0000-000000000000"
            ),
            account=CloudAccount(
                account_id="<AWS_ACCOUNT_ID>",
                region_name="us-west-2",
                account_name="Cirro Lab Project",
                account_type=CloudAccountType.BYOA
            ),
            contacts=[
                Contact(
                    name="Contact Name",
                    organization="Contact Organization",
                    email="contact@email.com",
                    phone="987-654-3210"
                )
            ]
        )

        # Hosted projects are managed by Cirro
        hosted_project = ProjectRequest(
            name="New Project Name",
            description="Description of new project",
            billing_account_id="billing-account-id",
            settings=ProjectSettings(
                budget_period=BudgetPeriod.MONTHLY,
                budget_amount=1000,
                max_spot_vcpu=300,
                service_connections=[],
                retention_policy_days=7
            ),
            contacts=[
                Contact(
                    name="Contact Name",
                    organization="Contact Organization",
                    email="contact@email.com",
                    phone="987-654-3210"
                )
            ]
        )

        cirro.projects.create(byoa_project)
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

    def set_user_role(self, project_id: str, username: str, role: ProjectRole, suppress_notification=False):
        """
        Sets a user's role within a project.

        Set to `ProjectRole.NONE` if removing the user from a project.

        Args:
            project_id (str): Project ID
            username (str): Username
            role (`cirro_api_client.v1.models.ProjectRole`): New role to apply
            suppress_notification (bool): Suppress email notification
        """
        request_body = SetUserProjectRoleRequest(
            username=username,
            role=role,
            suppress_notification=suppress_notification
        )
        set_user_project_role.sync_detailed(project_id=project_id, body=request_body, client=self._api_client)

    def archive(self, project_id: str):
        """
        Sets the project status to archived (hidden from active projects)

        Args:
            project_id (str): Project ID
        """
        archive_project.sync_detailed(project_id=project_id, client=self._api_client)

    def unarchive(self, project_id: str):
        """
        Sets the project status to active

        Args:
            project_id (str): Project ID
        """
        unarchive_project.sync_detailed(project_id=project_id, client=self._api_client)
