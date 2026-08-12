import asyncio
import random
from typing import Any

from bot.game.behaviors.attack import attack_mob
from bot.game.behaviors.buy import buy_item
from bot.game.behaviors.collect import collect_item
from bot.game.behaviors.craft import create_item, open_and_create_recipe
from bot.game.behaviors.equip import equip_item
from bot.game.behaviors.talk import talk_with_npc
from bot.game.entities.map import Map
from bot.game.entities.player import Player
from bot.game.entities.player_interactions import PlayerInteractions
from bot.game.entities.mob import Mob
from bot.game.services.map_services import a_star, find_path_to_or_near
from bot.game.services.mob_service import is_npc_walkover
from bot.game.services.move_service import follow_path, go_to_target
from bot.ui.botUI import BotUI
from bot.core.driver import MyDriver

DIALOG_TIMEOUT_SECONDS = 6.0
DIALOG_CLEAR_TIMEOUT_SECONDS = 8.0
DIALOG_CLEAR_POLL_SECONDS = 0.15


async def is_quest_enabled() -> bool:
    selections = await BotUI().get_selections()
    return selections.quest_enabled


async def should_abort_quest() -> bool:
    return not await is_quest_enabled()

async def _should_abort_or_stale(quest_before: dict) -> bool:
    if not await is_quest_enabled():
        return True
    quest_now = await fetch_active_quest_data()
    if quest_now.get("questId") != quest_before.get("questId"):
        return True
    if quest_now.get("targets") != quest_before.get("targets"):
        return True
    return False


# --- dialog guard ---
# Interceptor (inject_dialog_interceptor) sam wybiera opcje dialogowe przez
# MutationObserver + processDialogStep. Ta funkcja tylko odczekuje, aż okno
# dialogowe faktycznie się zamknie, zanim ruszymy dalej (dialogi lubią
# wyskakiwać automatycznie po zmianie mapy / przejściu przez bramkę).
async def wait_for_dialog_clear(
    timeout: float = DIALOG_CLEAR_TIMEOUT_SECONDS,
    poll: float = DIALOG_CLEAR_POLL_SECONDS,
) -> None:
    driver = await MyDriver().get_driver()
    elapsed = 0.0
    while elapsed < timeout:
        is_open = await driver.evaluate(
            "() => window.isDialogOpen ? window.isDialogOpen() : false",
            isolated_context=False,
        )
        if not is_open:
            return
        await asyncio.sleep(poll)
        elapsed += poll


async def inject_quest_observer() -> None:
    page = await MyDriver().get_driver()
    await page.evaluate(
        r"""
        (() => {
            if (window.BotQuestObserverInjected) return;
            window.BotQuestObserverInjected = true;
            // window.BotQuestTargets = window.BotQuestTargets || {
            //     KILL: [],
            //     TALK: null,
            //     COLLECT: null,
            //     WALK: null
            // };
            window.BotQuestTargets = window.BotQuestTargets || {};
            window.BotQuestTargets.KILL = window.BotQuestTargets.KILL || [];
            window.BotQuestTargets.TALK = window.BotQuestTargets.TALK ?? null;
            window.BotQuestTargets.COLLECT = window.BotQuestTargets.COLLECT ?? null;
            window.BotQuestTargets.WALK = window.BotQuestTargets.WALK ?? null;
            window._lastArrowSignature = window._lastArrowSignature || null;

            const NAV_LABEL_BLACKLIST = new Set(["Przejście"]);
            function looksLikeNavLabel(name) {
                if (!name) return false;
                return NAV_LABEL_BLACKLIST.has(name);
            }

            function tryInject() {
                if (!window.getEngine || !window.getEngine().targets) {
                    setTimeout(tryInject, 500);
                    return;
                }

                const targets = window.getEngine().targets;
                const originalAddArrow = targets.addArrow.bind(targets);

                if (!targets.originalAddArrow) {
                    targets.originalAddArrow = targets.addArrow.bind(targets);
                }

                targets.addArrow = function (arrowId, text, pos, goToPos, typeParent, arrowType, tooltipData) {
                    const signature = `${text}|${pos?.x}|${pos?.y}|${typeParent}`;
                    const isNewSignature = signature !== window._lastArrowSignature;
                    if (isNewSignature) {
                        window._lastArrowSignature = signature;
                        console.log("RAW ADDARROW:", { text, pos, goToPos, typeParent, arrowType, tooltipData });
                    }

                    const targetName = pos?.name || text;

                    if (looksLikeNavLabel(targetName)) {
                        return originalAddArrow(arrowId, text, pos, goToPos, typeParent, arrowType, tooltipData);
                    }

                    const lowerText = text?.toLowerCase?.() || "";
                    let kind = "UNKNOWN";

                    if (lowerText.includes("/")) kind = "KILL";
                    else if (tooltipData && tooltipData.src) kind = "COLLECT";
                    else if (tooltipData) kind = "TALK";
                    else kind = "WALK";

                    const newTarget = {
                        name: pos?.name || "???",
                        x: pos?.x || 0,
                        y: pos?.y || 0,
                        kind,
                        killCounter: null,
                        timestamp: Date.now()
                    };

                    if (kind === "KILL") {
                        window.BotQuestTargets.KILL = [];

                        const match = text.match(/\((\d+)\/(\d+)\)/);
                        if (match) {
                            const [_, current, toKill] = match;
                            newTarget.killCounter = { current: Number(current), toKill: Number(toKill) };

                            if (newTarget.killCounter.current < newTarget.killCounter.toKill) {
                                window.BotQuestTargets.KILL.push(newTarget);
                            } else if (isNewSignature) {
                                console.log(`%c🟩 [KILL] ${newTarget.name} — already completed (${newTarget.killCounter.current}/${newTarget.killCounter.toKill}), skip.`, "color:green;font-weight:bold;");
                            }
                        }
                    } else {
                        window.BotQuestTargets.KILL = [];
                        window.BotQuestTargets[kind] = newTarget;
                    }

                    if (isNewSignature) {
                        const colorMap = { KILL: "red", TALK: "cyan", COLLECT: "yellow" };
                        const color = colorMap[kind] || "white";
                        console.log(
                            `%c🎯 [${kind}] New target: ${newTarget.name} @(${newTarget.x},${newTarget.y}) killCounter=${JSON.stringify(newTarget.killCounter)}`,
                            `color:${color};font-weight:bold;`
                        );
                    }

                    return originalAddArrow(arrowId, text, pos, goToPos, typeParent, arrowType, tooltipData);
                };

                window.getEngine().questTracking.startTrackingIfActiveTrackingQuestExist();
                console.log("%c✅ Quest observer has been injected (TALK/COLLECT = last, KILL = list of only unfinished ones).", "color: cyan; font-weight: bold;");
            }

            tryInject();
        })();
        """,
        isolated_context=False,
    )


async def inject_dialog_interceptor() -> None:
    page = await MyDriver().get_driver()
    await page.evaluate(
        r"""
        (function() {
            const DIALOG_STALL_TIMEOUT = 1200;

            const REVERSE_BIT_MAP = {
                "line_cont_quest": 16,
                "line_option": 2,
                "line_new_quest": 8,
                "line_barter": 65536,
                "line_shop": 32,
                "line_exit": 4
            };

            if (typeof window._g !== 'function') {
                console.error("[BOT] Błąd krytyczny: Brak funkcji _g.");
                return;
            }

            if (window.botInitialized) {
                console.warn("[BOT] Interceptor jest już zainicjalizowany.");
                return;
            }

            window.original_g = window._g;
            const original_g = window.original_g;
            window.botInitialized = true;

            let lastNpcId = null;
            let dialogWatchdogTimer = null;
            let isProcessingDialog = false;
            let dialogCooldownUntil = 0;

            // Cache nieudanych opcji (aby nie zapętlać się w tym samym wyborze)
            window._failedDialogOptions = window._failedDialogOptions || {};

            window.isDialogOpen = function() {
                const dialogEl = document.querySelector('.dialogue-window, div.dialog, #dialog');
                if (!dialogEl) return false;
                const style = window.getComputedStyle(dialogEl);
                return style.display !== 'none' && style.visibility !== 'hidden' && dialogEl.offsetWidth > 0;
            };

            let wasDialogOpen = window.isDialogOpen();
            if (window._dialogCloseWatcherId) {
                clearInterval(window._dialogCloseWatcherId);
            }
            window._dialogCloseWatcherId = setInterval(() => {
                const nowOpen = window.isDialogOpen();
                if (wasDialogOpen && !nowOpen) {
                    // dialog właśnie się zamknął — zablokuj wszelkie próby klikania na 0.25s
                    dialogCooldownUntil = Date.now() + 250;
                    resetDialogWatchdog();
                    isProcessingDialog = false;
                    console.log("%c[BOT DIALOG] Okno zamknięte — pauza 0.25s przed kolejną akcją.", "color: #ffaa00; font-weight: bold;");
                } else if (nowOpen && Date.now() >= dialogCooldownUntil && !isProcessingDialog) {
                    window.processDialogStep();
                }
                wasDialogOpen = nowOpen;
            }, 150);

            function resetDialogWatchdog() {
                if (dialogWatchdogTimer) {
                    clearTimeout(dialogWatchdogTimer);
                    dialogWatchdogTimer = null;
                }
            }

            function startDialogWatchdog() {
                resetDialogWatchdog();
                dialogWatchdogTimer = setTimeout(() => {
                    if (Date.now() < dialogCooldownUntil) return; 
                    if (window.isDialogOpen() && lastNpcId) {
                        console.warn(`%c[BOT WATCHDOG] Dialog wciąż otwarty. Ponawiam próbę...`, 'color: orange; font-weight: bold;');
                        original_g(`talk&id=${lastNpcId}`);
                    }
                }, DIALOG_STALL_TIMEOUT);
            }

            function getDomOptions() {
                const elements = document.querySelectorAll(".dialogue-window-answer");
                const options = [];

                elements.forEach((el, index) => {
                    let text = el.querySelector(".answer-text")?.innerText || el.innerText;
                    let icon = el.querySelector(".icon");
                    let detectedBit = 2;

                    if (icon) {
                        for (let [cssClass, bit] of Object.entries(REVERSE_BIT_MAP)) {
                            if (icon.classList.contains(cssClass)) {
                                detectedBit = bit;
                                break;
                            }
                        }
                    }

                    options.push({
                        index: index + 1,
                        bit: detectedBit,
                        element: el,
                        text: text.trim()
                    });
                });

                return options;
            }

            let lastOptionsSignature = null;

            function optionsSignature(options) {
                return options.map(o => `${o.bit}:${o.text}`).join("|");
            }

            function selectBestDomOption(options) {
                if (!options || options.length === 0) return null;

                const signature = optionsSignature(options);
                const sameAsLast = signature === lastOptionsSignature;

                // Dialog poszedł dalej (inny zestaw opcji) -> czyścimy pamięć nieudanych prób
                if (!sameAsLast) {
                    window._failedDialogOptions[lastNpcId] = new Set();
                }
                lastOptionsSignature = signature;

                const npcCache = window._failedDialogOptions[lastNpcId] || new Set();
                const pool = options.filter(o => !npcCache.has(o.text));
                const finalPool = pool.length > 0 ? pool : options;

                let target = finalPool.find(o => o.bit === 16);
                if (target) return target;

                target = finalPool.find(o => o.bit === 8);
                if (target) return target;

                target = finalPool.find(o => o.bit === 2);
                if (target) return target;

                target = finalPool.find(o => o.bit === 4);
                return target || finalPool[0];
            }

            const DIALOG_CLICK_DELAY_MIN_MS = 150;
            const DIALOG_CLICK_DELAY_MAX_MS = 200;

            window.processDialogStep = function() {
                    if (Date.now() < dialogCooldownUntil) {
                        if (window.isDialogOpen()) {
                            const wait = dialogCooldownUntil - Date.now() + 50;
                            setTimeout(window.processDialogStep, wait);
                        }
                        return;
                    }

                if (!window.isDialogOpen()) {
                    isProcessingDialog = false;
                    resetDialogWatchdog();
                    return;
                }

                const options = getDomOptions();
                if (options.length === 0) {
                    isProcessingDialog = false;
                    return;
                }
                if (isProcessingDialog) return;
                isProcessingDialog = true;
                const best = selectBestDomOption(options);

                if (!best) {
                    isProcessingDialog = false;
                    return;
                }

                const clickDelay = DIALOG_CLICK_DELAY_MIN_MS + Math.random() * (DIALOG_CLICK_DELAY_MAX_MS - DIALOG_CLICK_DELAY_MIN_MS);

                setTimeout(() => {
                    // Dialog mógł się zmienić/zamknąć w trakcie oczekiwania — sprawdź jeszcze raz.
                    if (!window.isDialogOpen() || Date.now() < dialogCooldownUntil) {
                        isProcessingDialog = false;
                        return;
                    }

                    console.log(`%c[BOT DIALOG] Automatyczny wybór: Opcja ${best.index} | Bit: ${best.bit} | "${best.text}"`, "color: #00ff00; font-weight: bold;");

                    if (lastNpcId) {
                        if (!window._failedDialogOptions[lastNpcId]) {
                            window._failedDialogOptions[lastNpcId] = new Set();
                        }
                        window._failedDialogOptions[lastNpcId].add(best.text);
                    }

                    best.element.click();

                    resetDialogWatchdog();
                    startDialogWatchdog();
                    setTimeout(() => { isProcessingDialog = false; }, 350);
                }, clickDelay);
            };

            window._g = function(command, originalCallback, ...args) {
                if (typeof command === 'string' && command.startsWith('talk')) {
                    const currentNpcId = command.match(/id=([\d.-]+)/)?.[1] || null;
                    if (currentNpcId && currentNpcId !== lastNpcId) {
                        lastNpcId = currentNpcId;
                    }
                    resetDialogWatchdog();

                    const interceptedCallback = function(responseData) {
                        if (typeof originalCallback === 'function') {
                            originalCallback.apply(this, arguments);
                        }
                        setTimeout(window.processDialogStep, 1000);
                    };

                    return original_g(command, interceptedCallback, ...args);
                }
                return original_g.apply(this, arguments);
            };

            const observer = new MutationObserver((mutations) => {
                if (Date.now() < dialogCooldownUntil) return;
                for (const mutation of mutations) {
                    if (mutation.addedNodes.length > 0) {
                        if (window.isDialogOpen() && !isProcessingDialog) {
                            console.log("%c[BOT DETEKTOR] Wykryto automatyczne okno dialogowe!", "color: #cyan; font-weight: bold;");
                            setTimeout(window.processDialogStep, 500);
                            break;
                        }
                    }
                }
            });

            const targetContainer = document.querySelector('#game-layer') || document.body;
            observer.observe(targetContainer, { childList: true, subtree: true });

            console.log("%c[BOT] Interceptor dialogowy oraz Detektor Autostartu AKTYWNE.", 'color:lime;font-weight:bold;font-size:14px;');
        })();
        """,
        isolated_context=False,
    )

async def disable_quest_hooks() -> None:
    driver = await MyDriver().get_driver()
    await driver.evaluate(
        """
        (() => {
            if (window.BotQuestObserverInjected) delete window.BotQuestObserverInjected;

            const targets = window.getEngine?.().targets;
            if (targets?.originalAddArrow) {
                targets.addArrow = targets.originalAddArrow;
                delete targets.originalAddArrow;
            }

            if (window.getEngine()?.questTracking?.stopTracking) {
                window.getEngine().questTracking.stopTracking();
            }

            if (window.BotQuestTargets) window.BotQuestTargets = { KILL: [], TALK: null, COLLECT: null, WALK: null };
            console.log("%c🧹 Quest hooks deactivated and status cleared.", "color:orange;font-weight:bold;");
        })();
        """,
        isolated_context=False,
    )


async def disable_dialog_interceptor() -> None:
    driver = await MyDriver().get_driver()
    await driver.evaluate(
        """
        (() => {
            if (!window.botInitialized) return;

            if (window.original_g) {
                window._g = window.original_g;
                delete window.original_g;
            }

            delete window.botInitialized;
            console.log("%c🧹 Interceptor dialog deactivated.", "color: orange; font-weight: bold;");
        })();
        """,
        isolated_context=False,
    )


async def disable_all() -> None:
    await disable_dialog_interceptor()
    await disable_quest_hooks()


async def fetch_active_quest_data() -> dict[str, Any]:
    page = await MyDriver().get_driver()
    quest_data = await page.evaluate(
        """
        (() => {
            const engine = window.getEngine ? window.getEngine() : null;
            const activeQuestId = engine?.questTracking?.getActiveServerTrackingQuest?.() || null;
            let questTitle = null;
            let questItems = [];

            if (activeQuestId) {
                const data = engine?.quests?.getQuestData?.(activeQuestId);
                questTitle = data?.title || null;
                questItems = data?.itemsArray || [];
            }

            const rawTargets = window.BotQuestTargets || {};
            let normalizedTargets = [];

            let lastKillTime = rawTargets.KILL?.length ? Math.max(...rawTargets.KILL.map(k => k.timestamp)) : 0;
            let lastTalkTime = rawTargets.TALK?.timestamp || 0;
            let lastCollectTime = rawTargets.COLLECT?.timestamp || 0;
            let lastWalkTime = rawTargets.WALK?.timestamp || 0;
            let lastNpcTime = Math.max(lastTalkTime, lastCollectTime, lastWalkTime);

            if (lastKillTime > lastNpcTime) {
                normalizedTargets = [...rawTargets.KILL];
            } else if (lastTalkTime >= lastCollectTime && lastTalkTime >= lastWalkTime) {
                normalizedTargets = [rawTargets.TALK];
            } else if (lastCollectTime >= lastWalkTime) {
                normalizedTargets = [rawTargets.COLLECT];
            } else {
                normalizedTargets = [rawTargets.WALK];
            }

            return { questId: activeQuestId, questTitle, questItems, targets: normalizedTargets };
        })();
        """,
        isolated_context=False,
    )

    return quest_data or {
        "questId": None,
        "questTitle": None,
        "questItems": [],
        "targets": [],
    }


async def handle_quest_items(quest_items, shop_items) -> None:
    if not quest_items:
        return

    items_to_buy = [
        shop_item["id"]
        for q_item_name in quest_items
        for shop_item in shop_items
        if shop_item["name"].lower() == q_item_name.lower()
    ]

    if not items_to_buy:
        return

    await buy_item(items_to_buy, 1)


async def _resolve_target_flags(driver, goal) -> tuple[bool, bool]:
    has_renewable_npc = await driver.evaluate(
        f"() => !!window.getEngine?.().npcs?.getRenewableNpcByPosition({goal[0]}, {goal[1]})",
        isolated_context=False,
    )
    has_gateway = await driver.evaluate(
        f"() => !!window.getEngine?.().map?.gateways?.getGtwAtPosition({goal[0]}, {goal[1]})",
        isolated_context=False,
    )
    return has_renewable_npc, has_gateway


async def _resolve_mob_id(driver, target_mob: Mob, goal) -> str | None:
    mob_id = target_mob.id
    if mob_id:
        return mob_id

    npc_id_val = await driver.evaluate(
        f"""
        () => {{
            const all = window.Engine.npcs.check();
            for (const key in all) {{
                const d = all[key].d;
                if (d && d.x === {goal[0]} && d.y === {goal[1]}) {{
                    return d.id;
                }}
            }}
            return null;
        }}
        """,
        isolated_context=False,
    )
    if npc_id_val:
        target_mob.id = str(npc_id_val)
    return target_mob.id


async def _handle_shop_and_items(driver) -> None:
    barter_opened = await driver.evaluate(
        "(() => !!window.getEngine?.().barter)()", isolated_context=False
    )
    if barter_opened and await is_quest_enabled():
        print("⚙️ Open barter detected — item creation...")
        await create_item()
        await asyncio.sleep(random.uniform(0.8, 1.2))

    if not await is_quest_enabled():
        return

    shop_items = await driver.evaluate(
        """
        (() => {
            const shop = window.getEngine?.().shop?.getItems?.() || {};
            return Object.values(shop).map(item => ({
                name: item.getName(),
                id: item.getId()
            }));
        })();
        """,
        isolated_context=False,
    )
    if shop_items:
        print(f"🛒 Shop open ({len(shop_items)} items)")
        quest_data = await fetch_active_quest_data()
        await handle_quest_items(quest_data["questItems"], shop_items)

    if not await is_quest_enabled():
        return

    # new_items = await driver.evaluate(
    #     """
    #         (() => {
    #             const items = window.getEngine().items.fetchLocationItems("g");
    #             return items
    #                 .filter(item => item.getNow === true || item._cachedStats?.lootbox)
    #                 .filter(item => item.itemClType !== 15)
    #                 .filter(item => !item._cachedStats?.bag)
    #                 .filter(item => {
    #                     const type = item.getReqpStat();
    #                     const lvl = item.getLvlStat();
    #                     const hasRecipe = item._cachedStats?.recipe;
    #                     return type || lvl || hasRecipe;
    #                 })
    #                 .map(item => ({
    #                     id: item.id,
    #                     lvl: item.getLvlStat(),
    #                     hasRecipe: !!item._cachedStats?.recipe,
    #                     isLootbox: !!item._cachedStats?.lootbox,
    #                 }));
    #         })();
    #     """,
    #     isolated_context=False,
    # )

    new_items = await driver.evaluate(
        """
            (() => {
                const items = window.getEngine().items.fetchLocationItems("g");
                return items
                    .filter(item => item.getNow === true)
                    .filter(item => item._cachedStats?.quest)
                    .map(item => ({
                        id: item.id,
                        name: item.name,
                        lvl: item.getLvlStat ? item.getLvlStat() : null,
                        hasRecipe: !!item._cachedStats?.recipe,
                        isLootbox: !!item._cachedStats?.lootbox,
                        cachedStats: item._cachedStats,
                    }));
            })();
        """,
        isolated_context=False,
    )
    if not new_items:
        return
    print(f"🎯 Nowe itemki questowe: {[i['name'] for i in new_items]}")
    recipes = [i for i in new_items if i["hasRecipe"]]
    player = Player()
    hero_lvl = await player.lvl()
    equipables = [
        i for i in new_items if (i["lvl"] is None or hero_lvl >= int(i["lvl"]))
    ]

    if equipables:
        print(f"🧥 New items to equip: {len(equipables)}")
        await equip_item([i["id"] for i in equipables])

        lootboxes = [
            i for i in new_items if i.get("isLootbox") and hero_lvl >= int(i["lvl"])
        ]
        if lootboxes:
            actions = PlayerInteractions()
            await actions.accept_loot()

    if recipes and await is_quest_enabled():
        await open_and_create_recipe()
        await asyncio.sleep(random.uniform(0.8, 1.2))


async def _handle_talk(driver, path, mob_id, quest_before: dict) -> bool:
    """Zwraca True jeśli trzeba przerwać (abort)."""
    await wait_for_dialog_clear()
    await go_to_target(path, mob_id, mobType="quest", should_abort=lambda: _should_abort_or_stale(quest_before))
    await asyncio.sleep(random.uniform(0.4, 0.65))

    if not await is_quest_enabled():
        return True

    await wait_for_dialog_clear()
    quest_mid = await fetch_active_quest_data()
    if quest_mid.get("questId") != quest_before.get("questId") or quest_mid.get("targets") != quest_before.get("targets"):
        print("✅ Quest już przesunięty w trakcie dojścia (dialog obsłużony automatycznie) — pomijam jawne talk_with_npc.")
        player_interactions = PlayerInteractions()
        await player_interactions.is_fight_active()
        await _handle_shop_and_items(driver)
        return not await is_quest_enabled()

    try:
        await asyncio.wait_for(talk_with_npc(mob_id), timeout=DIALOG_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        quest_check = await fetch_active_quest_data()
        if quest_check.get("questId") != quest_before.get("questId") or quest_check.get("targets") != quest_before.get("targets"):
            print("✅ Timeout na talk_with_npc, ale quest i tak poszedł dalej (auto-dialog) — kontynuuję.")
        else:
            print(f"⏱️ talk_with_npc: brak odpowiedzi przez {DIALOG_TIMEOUT_SECONDS}s — przerywam akcję.")
            return True

    await wait_for_dialog_clear()
    await asyncio.sleep(random.uniform(0.8, 1.25))

    if not await is_quest_enabled():
        return True

    quest_after = await fetch_active_quest_data()
    if quest_after.get("questId") != quest_before.get("questId"):
        print(f"✅ Quest zmieniony po dialogu: {quest_before.get('questId')} → {quest_after.get('questId')}")
    elif quest_after.get("targets") != quest_before.get("targets"):
        print("✅ Cel questa zaktualizowany po dialogu — rozmowa faktycznie przesunęła quest dalej.")

    player_interactions = PlayerInteractions()
    await player_interactions.is_fight_active()

    await _handle_shop_and_items(driver)
    return not await is_quest_enabled()


async def execute_quest_target(map_2d, start, target_mob: Mob, kind: str) -> bool:
    map_ent = Map()
    kind = kind.upper()
    goal = target_mob.position
    driver = await MyDriver().get_driver()

    print(target_mob)

    path = find_path_to_or_near(map_2d, start, goal)
    if not path or len(path) < 2:
        return False

    try:
        walk_over = await is_npc_walkover(goal)
    except Exception:
        walk_over = False

    has_renewable_npc, has_gateway = await _resolve_target_flags(driver, goal)
    mob_id = await _resolve_mob_id(driver, target_mob, goal)

    await wait_for_dialog_clear()

    quest_before = await fetch_active_quest_data()

    async def _abort_check() -> bool:
        return await _should_abort_or_stale(quest_before)

    if kind == "WALK":
        current_map = await map_ent.get_current_map_id()
        await follow_path(path, current_map, should_abort=_abort_check)

    elif kind in ("TALK", "COLLECT"):
        if has_renewable_npc or has_gateway or walk_over:
            if has_renewable_npc:
                if not await go_to_target(
                    path, mob_id, mobType="gateway", should_abort=_abort_check
                ):
                    if await should_abort_quest():
                        return True
                await collect_item(goal)
            else:
                current_map = await map_ent.get_current_map_id()
                await follow_path(path, current_map, should_abort=_abort_check)
        elif not mob_id:
            print(f"ℹ️ {target_mob.name}: brak rozpoznanego NPC pod celem — traktuję jako WALK.")
            current_map = await map_ent.get_current_map_id()
            await follow_path(path, current_map, should_abort=_abort_check)
        else:
            aborted = await _handle_talk(driver, path, mob_id, quest_before)
            if aborted:
                return True

    elif kind == "KILL":
        if has_renewable_npc or has_gateway or walk_over:
            current_map = await map_ent.get_current_map_id()
            await follow_path(path, current_map, should_abort=_abort_check)
        else:
            if not await is_quest_enabled():
                return True
            result = await go_to_target(
                path, mob_id, mobType="quest", should_abort=_abort_check
            )
            print(result, mob_id, path, target_mob.name)
            if result:
                await wait_for_dialog_clear()
                if not await _abort_check():
                    await attack_mob(target_mob, heroes=False)

    await asyncio.sleep(random.uniform(0.8, 1.3))
    return False