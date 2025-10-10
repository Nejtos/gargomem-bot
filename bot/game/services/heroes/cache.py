from collections import OrderedDict
import time
from typing import Optional

from bot.game.services.heroes.config import EXIT_POS_CACHE_MAX, EXIT_POS_CACHE_TTL_SEC


_EXIT_POS_CACHE: OrderedDict[tuple[str, str], tuple[float, list[tuple[int, int]]]] = (
    OrderedDict()
)
_BFS_DIST_CACHE: OrderedDict[tuple[tuple, int, int], list[list[int]]] = OrderedDict()


def _exit_cache_get(
    cur_map_id: str, target_map_id: str
) -> Optional[list[tuple[int, int]]]:
    key = (str(cur_map_id), str(target_map_id))
    now = time.time()
    if key in _EXIT_POS_CACHE:
        ts, data = _EXIT_POS_CACHE[key]
        if now - ts <= EXIT_POS_CACHE_TTL_SEC:
            _EXIT_POS_CACHE.move_to_end(key)
            return list(data)
        else:
            _EXIT_POS_CACHE.pop(key, None)
    return None


def _exit_cache_put(
    cur_map_id: str, target_map_id: str, positions: list[tuple[int, int]]
):
    key = (str(cur_map_id), str(target_map_id))
    _EXIT_POS_CACHE[key] = (time.time(), list(positions))
    if len(_EXIT_POS_CACHE) > EXIT_POS_CACHE_MAX:
        _EXIT_POS_CACHE.popitem(last=False)
