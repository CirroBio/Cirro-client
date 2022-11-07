from typing import List


def filter_deleted(items: List) -> List:
    return list(filter(lambda item: not item.get('_deleted', False), items))
