import asyncio
import json
import random

from bot.game.navigation.helpers import get_current_map, get_gateway_pos, get_gateways
from bot.game.services.heroes.cache import _exit_cache_get, _exit_cache_put


def _pairs_from_flat_list(pos_list):
    pairs = []
    if not isinstance(pos_list, (list, tuple)):
        return pairs
    for i in range(0, len(pos_list) - 1, 2):
        try:
            x = int(pos_list[i])
            y = int(pos_list[i + 1])
            pairs.append((x, y))
        except Exception:
            continue
    return pairs


def _filter_gateways_for_target(gateways, target_id_str: str):
    ex = set()
    for g in gateways or []:
        gx = g.get("x") or g.get("tileX") or g.get("tx")
        gy = g.get("y") or g.get("tileY") or g.get("ty")
        tgt = (
            g.get("target")
            or g.get("mapId")
            or g.get("targetMapId")
            or g.get("targetMap")
            or g.get("to")
        )
        if gx is None or gy is None:
            continue
        if tgt is None:
            continue
        if str(tgt) == target_id_str:
            ex.add((int(gx), int(gy)))
    return list(ex)


async def wait_for_map_switch(
    prev_map: str, target_map: str, timeout: float = 60.0
) -> bool:
    target = str(target_map)
    start_t = asyncio.get_event_loop().time()
    while True:
        cur = str(await get_current_map())
        if cur == target:
            await asyncio.sleep(random.uniform(0.25, 0.45))
            return True
        if asyncio.get_event_loop().time() - start_t > timeout:
            return False
        await asyncio.sleep(0.5)


async def wait_for_gateways_ready(
    target_map_id: str,
    expect_next: str | None = None,
    timeout: float = 15.0,
    poll: float = 0.3,
) -> bool:
    target = str(target_map_id)
    want_next = str(expect_next) if expect_next is not None else None
    start_t = asyncio.get_event_loop().time()
    while True:
        cur = str(await get_current_map())
        if cur != target:
            if asyncio.get_event_loop().time() - start_t > timeout:
                return False
            await asyncio.sleep(poll)
            continue
        gateways = await get_gateways()
        if isinstance(gateways, list) and len(gateways) > 0:
            if want_next is None:
                return True
            try:
                gateways_js = json.dumps(gateways, ensure_ascii=False)
                pos_ok = False
                try:
                    want_next_int = int(want_next)
                except Exception:
                    want_next_int = None
                if want_next_int is not None:
                    pos = await get_gateway_pos(gateways_js, want_next_int)
                    if pos and len(pos) >= 2:
                        pos_ok = True
                if not pos_ok:
                    pos = await get_gateway_pos(gateways_js, json.dumps(want_next))
                    if pos and len(pos) >= 2:
                        pos_ok = True
                if pos_ok:
                    return True
            except Exception:
                pass
        if asyncio.get_event_loop().time() - start_t > timeout:
            return False
        await asyncio.sleep(poll)


def _exit_pairs_from_gateways_list(gateways):
    out = set()
    try:
        for g in gateways:
            gx = g.get("x") or g.get("tileX") or g.get("tx")
            gy = g.get("y") or g.get("tileY") or g.get("ty")
            tgt = (
                g.get("target")
                or g.get("mapId")
                or g.get("targetMapId")
                or g.get("targetMap")
                or g.get("to")
            )
            if gx is not None and gy is not None and tgt is not None:
                out.add((int(gx), int(gy)))
    except Exception:
        pass
    return list(out)


async def collect_exit_positions_for_target(
    next_map_id, retries: int = 8, delay: float = 0.25
):
    try:
        cur_map_id = str(await get_current_map())
    except Exception:
        cur_map_id = None

    if cur_map_id is not None:
        cached = _exit_cache_get(cur_map_id, str(next_map_id))
        if cached is not None:
            return cached

    out = set()
    next_as_int = None
    try:
        next_as_int = int(str(next_map_id))
    except Exception:
        pass

    for _ in range(retries):
        try:
            gateways = await get_gateways()
            if not isinstance(gateways, list) or not gateways:
                await asyncio.sleep(delay)
                continue
            gateways_js = json.dumps(gateways, ensure_ascii=False)

            if next_as_int is not None:
                try:
                    pos = await get_gateway_pos(gateways_js, next_as_int)
                    for p in _pairs_from_flat_list(pos):
                        out.add((int(p[0]), int(p[1])))
                except Exception:
                    pass

            try:
                pos = await get_gateway_pos(gateways_js, json.dumps(str(next_map_id)))
                for p in _pairs_from_flat_list(pos):
                    out.add((int(p[0]), int(p[1])))
            except Exception:
                pass

            if not out:
                filtered = _filter_gateways_for_target(gateways, str(next_map_id))
                if filtered:
                    out.update(filtered)

            if out:
                res = list(out)
                if cur_map_id is not None:
                    _exit_cache_put(cur_map_id, str(next_map_id), res)
                return res

        except Exception:
            pass
        await asyncio.sleep(delay)

    res = list(out)
    if cur_map_id is not None:
        _exit_cache_put(cur_map_id, str(next_map_id), res)
    return res
