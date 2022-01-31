from typing import List


def get_id_from_name(items, name_or_id) -> str:
    matched = next((p for p in items if p['id'] == name_or_id), None)
    if matched:
        return matched['id']
    return next(p for p in items if p['name'] == name_or_id)['id']


def filter_deleted(items: List) -> List:
    return list(filter(lambda item: not item.get('_deleted', False), items))
