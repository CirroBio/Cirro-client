from gql import gql

from pubweb.clients.utils import get_id_from_name, filter_deleted
from pubweb.services.base import BaseService


def get_bucket(project_id):
    return f'z-{project_id}'


class ProjectService(BaseService):
    def list(self):
        query = gql('''
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
        ''')

        resp = self._api_client.query(query)['listProjects']
        return filter_deleted(resp['items'])

    def get_project_id(self, name_or_id: str) -> str:
        return get_id_from_name(self.list(), name_or_id)
