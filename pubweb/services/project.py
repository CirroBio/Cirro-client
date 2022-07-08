from typing import List, Optional

from pubweb.clients.utils import filter_deleted
from pubweb.file_utils import filter_files_by_pattern
from pubweb.models.file import FileAccessContext
from pubweb.models.project import Project
from pubweb.models.reference import Reference, References
from pubweb.services.file import FileEnabledService


class ProjectService(FileEnabledService):
    def list(self) -> List[Project]:
        """
        Gets a list of projects that you have access to
        """
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
        items = filter_deleted(resp['items'])
        return [Project.from_record(item) for item in items]

    def find_by_name(self, name: str) -> Optional[Project]:
        """
        Finds a project by name
        """
        return next((p for p in self.list() if p.name == name), None)

    def get_references(self, project_id: str, reference_directory: str) -> References:
        """
        Gets a list of references available for a given project and reference directory
        """
        access_context = FileAccessContext.download_project_resources(project_id)
        resources = self._file_service.get_file_listing(access_context)
        reference_files = filter_files_by_pattern(resources, f'data/references/{reference_directory}/*/*')
        references = [Reference.of(file) for file in reference_files]
        return References(references)
