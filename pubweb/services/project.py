from typing import List, Optional

from pubweb.clients.utils import get_id_from_name, filter_deleted
from pubweb.file_utils import filter_files_by_pattern
from pubweb.helpers.constants import REFERENCES_PATH_S3
from pubweb.models.file import FileAccessContext
from pubweb.models.project import Project
from pubweb.models.reference import Reference, References, ReferenceType
from pubweb.services.base import BaseService
from pubweb.services.file import FileEnabledMixin


class ProjectService(FileEnabledMixin, BaseService):
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

    def get_project_id(self, name_or_id: str) -> str:
        # TODO: move this out into CLI module
        return get_id_from_name(self.list(), name_or_id)

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
        reference_files = filter_files_by_pattern(resources, f'{REFERENCES_PATH_S3}/{reference_directory}/*/*')
        references = [Reference.of(file) for file in reference_files]
        return References(references)

    def add_reference(self, project_id: str, reference_name: str,
                      reference_files: List[str], reference_type: ReferenceType):
        access_context = FileAccessContext.upload_project_resources(project_id)
        file_name = ''
        destination_path = f'{REFERENCES_PATH_S3}/{reference_type.directory}/{reference_name}'
        self._file_service.upload_files(access_context, destination_path)
