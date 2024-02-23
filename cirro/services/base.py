from abc import ABC
from typing import TypeVar, Callable, Generic, Optional, List

from attr import define
from cirro_api_client import CirroApiClient

D = TypeVar('D')


@define
class PageResp(Generic[D]):
    data: D
    next_token: str


@define
class PageArgs:
    next_token: str
    limit: int


T = TypeVar('T', bound=PageResp)


def get_all_records(records_getter: Callable[[PageArgs], Optional[PageResp[D]]],
                    batch_size=5000, max_items=None) -> List[D]:
    next_token = None
    items = []

    while True:
        resp = records_getter(PageArgs(next_token=next_token, limit=batch_size))
        if not resp:
            return items

        items.extend(resp.data)

        next_token = resp.next_token
        if not next_token:
            return items

        if max_items and len(items) >= max_items:
            return items


@define
class BaseService(ABC):
    """
    Not to be instantiated directly
    """
    _api_client: CirroApiClient
