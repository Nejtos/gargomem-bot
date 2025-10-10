from bot.game.services.heroes.config import WORLD_JSON_PATH
from bot.game.services.heroes.world_graph import load_world_graph
from bot.data.heroes_data import heroes_dict


def has_resp_here(hero: str, map_id: str) -> bool:
    return bool(list(heroes_dict[hero]["maps"].get(str(map_id), [])))


def is_region_map(hero: str, map_id: str) -> bool:
    try:
        cfg = heroes_dict.get(hero) or {}
    except Exception:
        return False
    regions = cfg.get("region_maps") or cfg.get("regions") or []
    return str(map_id) in {str(x) for x in regions}


def region_children_for(hero: str, hub_map_id: str, graph=None) -> list[str]:
    try:
        cfg = heroes_dict.get(hero) or {}
    except Exception:
        cfg = {}
    by_hub = cfg.get("region_hubs") or {}
    kids_cfg = by_hub.get(str(hub_map_id))
    if kids_cfg:
        kids = [str(x) for x in kids_cfg]
    else:
        try:
            g = graph or load_world_graph(WORLD_JSON_PATH, directed=True)
        except Exception:
            g = {}
        raw = list(g.get(str(hub_map_id), []) or [])
        kids = [str(x) for x in raw if has_resp_here(hero, x)]
    kids = [k for k in kids if not is_region_map(hero, k)]
    return kids


def hero_region_maps_set(hero: str) -> set[str]:
    try:
        cfg = heroes_dict.get(hero) or {}
    except Exception:
        cfg = {}
    regs = cfg.get("region_maps") or cfg.get("regions") or []
    return {str(x) for x in regs}


def region_hubs_for(
    hero: str, region_map_id: str, graph=None, rev_graph=None
) -> list[str]:
    """
    Zwraca listę hubów (parterów) dla regionu WYŁĄCZNIE z heroes_data['region_hubs'].
    Jeśli brak wpisu – traktujemy, że region nie ma hubów.
    """
    region_id = str(region_map_id)
    try:
        cfg = heroes_dict.get(hero) or {}
    except Exception:
        cfg = {}

    by_region = cfg.get("region_hubs") or {}
    if isinstance(by_region, dict) and region_id in by_region:
        hubs_raw = by_region.get(region_id) or []
        return [str(x) for x in hubs_raw]
    return []
