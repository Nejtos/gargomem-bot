import asyncio
import random
from typing import Optional
from bot.game.services.heroes.config import HERO_RESPAWN_WINDOWS
from bot.game.services.heroes.grid_utils import _grid_is_valid
from bot.utils.helpers import current_location_map, current_position


async def safe_currentLocationMap(max_retries: int = 40, delay: float = 0.15):
    last_exc = None
    for _ in range(max_retries):
        try:
            grid = await current_location_map()
            if _grid_is_valid(grid):
                return grid
        except Exception as e:
            last_exc = e
        await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("currentLocationMap not ready (grid invalid)")


async def safe_current_position(
    max_retries: int = 40, delay: float = 0.12
) -> Optional[tuple[int, int]]:
    for _ in range(max_retries):
        try:
            pos = await current_position()
            if not pos or len(pos) < 2:
                await asyncio.sleep(delay)
                continue
            sx, sy = pos[0], pos[1]
            if sx is None or sy is None:
                await asyncio.sleep(delay)
                continue
            ix, iy = int(sx), int(sy)
            return ix, iy
        except Exception:
            await asyncio.sleep(delay)
        try:
            await safe_currentLocationMap(max_retries=1, delay=delay)
        except Exception:
            pass
    return None


def random_empty_cycle_wait_seconds() -> int:
    return int(random.randint(6, 10) * 60)


def get_hero_respawn_window(hero_key: str) -> tuple[int, int]:
    return HERO_RESPAWN_WINDOWS.get(hero_key, (3600, 10800))


def get_hero_min_respawn_seconds(hero_key: str) -> int:
    return int(get_hero_respawn_window(hero_key)[0])
