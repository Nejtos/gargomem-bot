import json
from typing import Optional, Tuple
from bot.core.driver import MyDriver
from bot.game.services.heroes.config import (
    HERO_DISPLAY_NAME,
    HERO_FIXED_ID,
    HERO_NEAR_RADIUS_TILES,
)
from bot.game.services.heroes.grid_utils import manhattan
from bot.game.services.heroes.utils import safe_currentLocationMap
from bot.utils.helpers import get_npc_id
from bot.data.heroes_data import heroes_dict


async def engine_get_npc_by_id(npc_id: int | str):
    page = await MyDriver().get_driver()
    try:
        literal = int(str(npc_id))
    except Exception:
        literal = json.dumps(str(npc_id))
    script = f"""
    (() => {{
        try {{
            const idArg = {literal};
            const npc = window.Engine?.npcs?.getById?.(idArg);
            if (!npc) return null;
            const d = npc.d || {{}};
            return {{ id: d.id ?? null, x: d.x ?? null, y: d.y ?? null, nick: d.nick ?? null, tpl: d.tpl ?? null, type: d.type ?? null }};
        }} catch (e) {{ return null; }}
    }})();
    """
    res = await page.evaluate(script, isolated_context=False)
    return res if isinstance(res, dict) else None


async def check_hero_presence_on_map(
    hero_key: str,
) -> tuple[bool, Optional[Tuple[int, int]], Optional[Tuple[int, int]], Optional[str]]:
    fixed_id = HERO_FIXED_ID.get(hero_key)
    if fixed_id is None:
        return False, None, None, None
    data = await engine_get_npc_by_id(fixed_id)
    if not data:
        return False, None, None, None
    try:
        x = int(data.get("x"))
        y = int(data.get("y"))
    except Exception:
        x = data.get("x")
        y = data.get("y")
    return (
        True,
        int(data.get("id")),
        (x, y) if x is not None and y is not None else None,
        data.get("nick"),
    )


def _gen_neighborhood(
    center: tuple[int, int], radius: int, grid
) -> list[tuple[int, int]]:
    if not center:
        return []
    rows, cols = len(grid), len(grid[0])
    cx, cy = int(center[0]), int(center[1])
    out: list[tuple[int, int]] = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if abs(dx) + abs(dy) <= radius:
                x, y = cx + dx, cy + dy
                if 0 <= x < rows and 0 <= y < cols:
                    out.append((x, y))
    if center not in out:
        out.append(center)
    return out


async def detect_hero_near_coordinate(
    hero_key: str,
    coord: tuple[int, int],
    radius: int = HERO_NEAR_RADIUS_TILES,
    preloaded_grid=None,
) -> tuple[
    bool, Optional[int], Optional[Tuple[int, int]], Optional[str], Optional[str]
]:
    display = HERO_DISPLAY_NAME.get(hero_key, hero_key)
    found, fixed_id, fixed_pos, fixed_nick = await check_hero_presence_on_map(hero_key)

    #  Szybki check: tylko sprawdzamy, czy coś w pobliżu respa
    if found and fixed_pos and manhattan(fixed_pos, coord) <= radius:
        # ale zanim zwrócimy -> pobierzemy PRECYZYJNE kordy z engine
        info = await engine_get_npc_by_id(fixed_id)
        pos = None
        mob_type = None
        if info:
            if info.get("x") is not None and info.get("y") is not None:
                pos = (int(info["x"]), int(info["y"]))
            mob_type = info.get("type")
        return True, fixed_id, pos, (fixed_nick or display), mob_type

    # Jeśli szybki check się nie udał – skanuj normalnie okolice
    grid = (
        preloaded_grid
        if preloaded_grid is not None
        else await safe_currentLocationMap()
    )
    around = _gen_neighborhood(coord, radius, grid)
    if not around:
        return False, None, None, None, None
    mob_id2, mob_type = await get_npc_id(tuple(around))
    if not mob_id2:
        return False, None, None, None, None

    fixed_id = HERO_FIXED_ID.get(hero_key)
    if fixed_id and mob_id2 == fixed_id:
        info = await engine_get_npc_by_id(mob_id2)
        pos = None
        if info and info.get("x") is not None and info.get("y") is not None:
            pos = (int(info["x"]), int(info["y"]))
        return (
            True,
            int(mob_id2),
            pos,
            (info.get("nick") if info else display),
            mob_type,
        )

    info = await engine_get_npc_by_id(mob_id2)
    if info and str(info.get("nick", "")).strip().lower() == display.strip().lower():
        pos = None
        if info.get("x") is not None and info.get("y") is not None:
            pos = (int(info["x"]), int(info["y"]))
        return (
            True,
            int(info.get("id")),
            pos,
            info.get("nick"),
            info.get("type") or mob_type,
        )

    return False, None, None, None, None


async def detect_hero_near_any_respawn_on_map(
    hero_key: str,
    map_id: str,
    radius: int = HERO_NEAR_RADIUS_TILES,
    preloaded_grid=None,
):
    respawns = list(heroes_dict[hero_key]["maps"].get(str(map_id), []))
    if not respawns:
        return False, None, None, None, None
    found_map, npc_id_map, npc_pos, npc_name = await check_hero_presence_on_map(
        hero_key
    )
    if found_map and npc_pos:
        for rp in respawns:
            if manhattan(npc_pos, rp) <= radius:
                return True, npc_id_map, npc_pos, npc_name, None
    grid = (
        preloaded_grid
        if preloaded_grid is not None
        else await safe_currentLocationMap()
    )
    for rp in respawns:
        ok, npc_id, pos, nick, mob_type = await detect_hero_near_coordinate(
            hero_key, rp, radius, preloaded_grid=grid
        )
        if ok:
            return True, npc_id, pos, nick, mob_type
    return False, None, None, None, None
