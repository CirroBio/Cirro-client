from typing import List

from pubweb.clients.utils import get_id_from_name, filter_deleted
from pubweb.models.process import Executor, Process
from pubweb.services.base import BaseService


class ProcessService(BaseService):
    def list(self, process_type: Executor = None) -> List[Process]:
        query = '''
          query ListProcesses(
            $filter: ModelProcessFilterInput
            $limit: Int
            $nextToken: String
          ) {
            listProcesses(filter: $filter, limit: $limit, nextToken: $nextToken) {
              items {
                id
                name
                desc
                _deleted
              }
            }
          }
        '''
        item_filter = {}
        if process_type:
            item_filter['executor'] = {'eq': process_type.value}
        resp = self._api_client.query(query, variables={'filter': item_filter})['listProcesses']
        return filter_deleted(resp['items'])

    def get_process_id(self, name_or_id: str) -> str:
        return get_id_from_name(self.list(), name_or_id)
