from typing import List, Optional

from cirro_api_client.v1.models import Reference


class References(List[Reference]):
    def find_by_name(self, name: str) -> Optional[Reference]:
        return next((ref for ref in self if ref.name == name), None)
