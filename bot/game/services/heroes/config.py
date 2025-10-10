USE_LOCAL_ASTAR = True
WORLD_JSON_PATH = "bot/data/world_maps.json"
DECISION_WAIT_SECONDS = 120

HERO_DISPLAY_NAME = {
    "Domina": "Domina Ecclesiae",
    "Patryk": "Mroczny Patryk",
    "Karmazyn": "Karmazynowy Mściciel",
    "Złodziej": "Złodziej",
}

HERO_FIXED_ID = {
    "Domina": 81268,
    "Patryk": 17405,
    "Karmazyn": 17439,
    "Złodziej": 40601,
}

HERO_RESPAWN_WINDOWS = {
    "Domina": (3600, 10800),
    "Patryk": (8100, 24300),
    "Karmazyn": (8100, 24300),
    "Złodziej": (8100, 24300),
}

HERO_NEAR_RADIUS_TILES = 10
RESTART_CYCLE_SIGNAL = "restart_cycle"

APPROACH_RESP_RADIUS_TILES = 9
DECISION_TIMEOUT_SECONDS = 20
WAIT_ON_CHOOSE_SECONDS = 90

INF_BIG = 10**9

EXIT_POS_CACHE_TTL_SEC = 30.0
EXIT_POS_CACHE_MAX = 256
BFS_DIST_CACHE_MAX = 32

SUB_ENTRY_LIMIT = 2

REPLAN_SMALL = 1
REPLAN_MEDIUM = 2
REPLAN_LARGE = 3
REPLAN_THRESHOLDS = (15, 27)  # (19, 27)

HERO_STRICT_SINGLE_PARENT = False
