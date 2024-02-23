from typing import List

from cirro_api_client.v1.api.metadata import get_project_samples, get_project_schema, update_project_schema, \
    update_sample
from cirro_api_client.v1.models import FormSchema, SampleRequest, Sample

from cirro.services.base import BaseService, get_all_records


class MetadataService(BaseService):
    """
    Service for interacting with the Metadata endpoints
    """
    def get_project_samples(self, project_id: str, max_items: int = 10000) -> List[Sample]:
        """
        Retrieves a list of samples associated with a project along with their metadata

        Args:
            project_id (str): ID of the Project
            max_items (int): Maximum number of records to get (default 10,000)
        """
        return get_all_records(
            records_getter=lambda page_args: get_project_samples.sync(project_id=project_id,
                                                                      client=self._api_client,
                                                                      next_token=page_args.next_token,
                                                                      limit=page_args.limit),
            max_items=max_items
        )

    def get_project_schema(self, project_id: str) -> FormSchema:
        """
        Get project metadata schema

        Args:
            project_id (str): ID of the Project
        """
        return get_project_schema.sync(project_id=project_id, client=self._api_client)

    def update_project_schema(self, project_id: str, schema: FormSchema):
        """
        Update project metadata schema

        Args:
            project_id (str): ID of the Project
            schema (cirro_api_client.v1.models.FormSchema): Metadata schema
        """
        update_project_schema.sync_detailed(project_id=project_id, body=schema, client=self._api_client)

    def update_sample(self, project_id: str, sample_id: str, sample: SampleRequest) -> Sample:
        """
        Updates metadata information for sample

        Args:
            project_id (str): ID of the Project
            sample_id (str): ID of the sample
            sample (cirro_api_client.v1.models.SampleRequest): Metadata information for the sample
        """
        return update_sample.sync(
            project_id=project_id,
            sample_id=sample_id,
            body=sample,
            client=self._api_client
        )
