from typing import List

from pubweb.api.models.reference import ReferenceType
from pubweb.api.services.base import BaseService


class CommonService(BaseService):
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

    # TODO: Global reference catalogue
