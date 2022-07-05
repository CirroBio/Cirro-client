from typing import List

from pubweb.clients.utils import get_id_from_name, filter_deleted
from pubweb.file_utils import filter_files_by_pattern
from pubweb.models.file import FileAccessContext
from pubweb.models.project import Project
from pubweb.models.reference import ReferenceType, Reference, References
from pubweb.services.file import FileEnabledService


class ProjectService(FileEnabledService):
    def list(self) -> List[Project]:
        query = '''
          query ListProjects(
            $filter: ModelProjectFilterInput
            $limit: Int
            $nextToken: String
          ) {
            listProjects(filter: $filter, limit: $limit, nextToken: $nextToken) {
              items {
                id
                name
                desc
                _deleted
              }
            }
          }
        '''

        resp = self._api_client.query(query)['listProjects']
        return filter_deleted(resp['items'])

    def get_project_id(self, name_or_id: str) -> str:
        return get_id_from_name(self.list(), name_or_id)

    def get_references_types(self) -> List[ReferenceType]:
        """
        Gets a list of available reference types
        """
        query = '''
          query GetReferenceTypes {
            getReferenceTypes {
              name
              description
              directory
              validation
            }
          }
        '''
        resp = self._api_client.query(query)['getReferenceTypes']
        return [ReferenceType.from_record(record) for record in resp]

    def get_references(self, project_id: str, reference_directory: str) -> References:
        """
        Gets a list of references available for a given project and reference directory
        """
        access_context = FileAccessContext.download_project_resources(project_id)
        resources = self._file_service.get_file_listing(access_context)
        reference_files = filter_files_by_pattern(resources, f'data/references/{reference_directory}/*/*')
        references = [Reference.of(file) for file in reference_files]
        return References(references)
