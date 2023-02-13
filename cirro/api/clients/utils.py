from typing import List

from cirro.api.models.status import Status


def filter_deleted(items: List) -> List:
    return list(filter(lambda item: item.get('status') != Status.DELETED.value, items))
