import asyncio
import random
from bot.game.interactions.attack import _auto_fight_if_active, attack_mob
from bot.game.moving.moving import go_to_target
from bot.game.moving.pathfiding import a_star
from bot.game.navigation.helpers import get_current_map
from bot.game.navigation.maps import follow_path
from bot.utils.dialogues import talk_with_npc
from bot.utils.helpers import (
    accept_loot,
    current_location_map,
    current_position,
    find_nearest_mob,
    get_hero_lvl,
    get_npc_id,
    is_npc_walkover,
)
from bot.utils.items import (
    buy_item,
    collect_item,
    create_item,
    equip_item,
    open_and_create_recipe,
)
from bot.ui.botUI import get_quest_enabled, set_selected_exp_to_new_value
from bot.core.driver import MyDriver


async def inject_quest_observer():
    page = await MyDriver().get_driver()
    await page.evaluate(
        r"""
        (() => {
            if (window.BotQuestObserverInjected) return;
            window.BotQuestObserverInjected = true;
            window.BotQuestTargets = window.BotQuestTargets || {
                KILL: [],
                TALK: null,
                COLLECT: null
            };

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

                targets.addArrow = function (t, text, pos, type, arg1, arg2) {
                    const lowerText = text?.toLowerCase?.() || "";
                    let kind = "UNKNOWN";

                    if (lowerText.includes("/")) kind = "KILL";
                    else if (arg2 && arg2.src) kind = "COLLECT";
                    else kind = "TALK";

                    const newTarget = {
                        name: pos?.name || "???",
                        x: pos?.x || 0,
                        y: pos?.y || 0,
                        kind,
                        killCounter: null,
                        timestamp: Date.now()
                    };

                    if (kind === "KILL") {
                        const match = text.match(/\((\d+)\/(\d+)\)/);
                        if (match) {
                            const [_, current, toKill] = match;
                            newTarget.killCounter = { current: Number(current), toKill: Number(toKill) };
                        }
                    }

                    if (kind === "KILL") {
                        window.BotQuestTargets.KILL = [];

                        const match = text.match(/\((\d+)\/(\d+)\)/);
                        if (match) {
                            const [_, current, toKill] = match;
                            newTarget.killCounter = { current: Number(current), toKill: Number(toKill) };

                            if (newTarget.killCounter.current < newTarget.killCounter.toKill) {
                                window.BotQuestTargets.KILL.push(newTarget);
                            } else {
                                console.log(`%c🟩 [KILL] ${newTarget.name} — already completed (${newTarget.killCounter.current}/${newTarget.killCounter.toKill}), skip.`, "color:green;font-weight:bold;");
                            }
                        }
                    } else {
                        window.BotQuestTargets.KILL = [];
                        window.BotQuestTargets[kind] = newTarget;
                    }

                    const colorMap = { KILL: "red", TALK: "cyan", COLLECT: "yellow" };
                    const color = colorMap[kind] || "white";
                    console.log(
                        `%c🎯 [${kind}] New target: ${newTarget.name} @(${newTarget.x},${newTarget.y}) killCounter=${JSON.stringify(newTarget.killCounter)}`,
                        `color:${color};font-weight:bold;`
                    );

                    return originalAddArrow(t, text, pos, type, arg1, arg2);
                };

                window.getEngine().questTracking.startTrackingIfActiveTrackingQuestExist();
                console.log("%c✅ Quest observer has been injected (TALK/COLLECT = last, KILL = list of only unfinished ones).", "color: cyan; font-weight: bold;");
            }

            tryInject();
        })();
        """,
        isolated_context=False,
    )


async def inject_dialog_interceptor():
    page = await MyDriver().get_driver()
    await page.evaluate(
        r"""
        (function() {
            const DIALOG_STALL_TIMEOUT = 1000;
            const FLAG_PLAYER_OPTION = 2;
            const FLAG_EXIT = 4;
            const FLAG_NEW_QUEST = 8;
            const FLAG_CONTINUE_QUEST = 16;

            if (typeof window._g !== 'function') {
                console.error("[BOT] Critical error: Function _g not found.");
                return;
            }

            if (window.botInitialized) {
                console.warn("[BOT] Bot already initialized.");
                return;
            }

            window.original_g = window._g;
            const original_g = window.original_g;
            window.botInitialized = true;
            console.log("[BOT] Original function _g saved.");

            let lastNpcId = null;
            let dialogWatchdogTimer = null;

            function resetDialogWatchdog() {
                if (dialogWatchdogTimer) {
                    clearTimeout(dialogWatchdogTimer);
                    dialogWatchdogTimer = null;
                }
            }

            function startDialogWatchdog() {
                resetDialogWatchdog();
                dialogWatchdogTimer = setTimeout(() => {
                    const isDialogOpen = document.querySelector('div.dialog, #dialog, ul.answers');
                    if (isDialogOpen && lastNpcId) {
                        console.warn(`%c[BOT] WATCHDOG: The dialog seems to be stuck (${DIALOG_STALL_TIMEOUT}ms). Forcing refresh...`, 'color: red; font-weight: bold;');
                        original_g(`talk&id=${lastNpcId}`);
                    }
                }, DIALOG_STALL_TIMEOUT);
            }

            function parseDialogData(flatData) {
                if (!Array.isArray(flatData)) return [];
                const options = [];
                for (let i = 0; i < flatData.length; i += 3) {
                    options.push({ flag: parseInt(flatData[i], 10), text: flatData[i + 1], id: flatData[i + 2] });
                }
                return options.filter(opt => opt.id && (opt.flag & (FLAG_PLAYER_OPTION | FLAG_NEW_QUEST | FLAG_CONTINUE_QUEST | FLAG_EXIT)));
            }

            function chooseBestOption(options) {
                if (!options || options.length === 0) return null;
                if (options.length === 1) {
                    const o = options[0];
                    o.type = o.flag & FLAG_EXIT ? "Only option: termination (API)" : "Only option: continuation (API)";
                    return o;
                }

                const nonExit = options.filter(o => !(o.flag & FLAG_EXIT));
                const continueQuest = nonExit.find(o => o.flag & FLAG_CONTINUE_QUEST);
                if (continueQuest) { continueQuest.type = "Priority: quest continuation"; return continueQuest; }

                const newQuest = nonExit.find(o => o.flag & FLAG_NEW_QUEST);
                if (newQuest) { newQuest.type = "Priority: new Quest"; return newQuest; }

                if (nonExit.length > 0) { const c = nonExit[nonExit.length - 1]; c.type = "Continue dialogue (default)"; return c; }

                const exitOption = options.find(o => o.flag & FLAG_EXIT);
                if (exitOption) { exitOption.type = "Forced termination (EXIT only)"; return exitOption; }

                return options[options.length - 1];
            }

            function processDialog(responseData) {
                const apiOptions = parseDialogData(responseData?.d);
                const bestApiChoice = chooseBestOption(apiOptions);

                if (bestApiChoice) {
                    const nextCommand = `talk&id=${lastNpcId}&c=${bestApiChoice.id}`;
                    console.log(`[BOT] Sending command: ${nextCommand}`);
                    original_g(nextCommand);
                    resetDialogWatchdog();
                    startDialogWatchdog();
                    return;
                }

                const domOptions = Array.from(document.querySelectorAll('ul.answers > li'));
                if (domOptions.length === 1) {
                    domOptions[0].click();
                    resetDialogWatchdog();
                    startDialogWatchdog();
                    return;
                }

                resetDialogWatchdog();
            }

            window._g = function(command, originalCallback, ...args) {
                if (typeof command === 'string' && command.startsWith('talk')) {
                    const currentNpcId = command.match(/id=([\d.-]+)/)?.[1] || null;
                    if (currentNpcId) lastNpcId = currentNpcId;

                    resetDialogWatchdog();

                    const interceptedCallback = function(responseData) {
                        if (typeof originalCallback === 'function') {
                            originalCallback.apply(this, arguments);
                        }
                        setTimeout(() => processDialog(responseData), 50);
                    };

                    return original_g(command, interceptedCallback, ...args);
                }
                return original_g.apply(this, arguments);
            };

            console.log("%c[BOT] Interceptor dialog ACTIVATED", 'color:lime;font-weight:bold;font-size:16px;');
        })();
        """,
        isolated_context=False,
    )


async def fetch_active_quest_data():
    page = await MyDriver().get_driver()
    quest_data = await page.evaluate(
        """
        (() => {
            const activeQuestId = window.Engine?.questTracking?.getActiveServerTrackingQuest?.() || null;
            let questTitle = null;
            let questItems = [];

            if (activeQuestId) {
                const data = window.Engine?.quests?.getQuestData?.(activeQuestId);
                questTitle = data?.title || null;
                questItems = data?.itemsArray || [];
            }

            const rawTargets = window.BotQuestTargets || {};
            let normalizedTargets = [];

            let lastKillTime = rawTargets.KILL?.length ? Math.max(...rawTargets.KILL.map(k => k.timestamp)) : 0;
            let lastTalkTime = rawTargets.TALK?.timestamp || 0;
            let lastCollectTime = rawTargets.COLLECT?.timestamp || 0;
            let lastNpcTime = Math.max(lastTalkTime, lastCollectTime);

            if (lastKillTime > lastNpcTime) {
                normalizedTargets = [...rawTargets.KILL];
            } else if (lastTalkTime >= lastCollectTime) {
                normalizedTargets = [rawTargets.TALK];
            } else {
                normalizedTargets = [rawTargets.COLLECT];
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


async def quest_service():
    print("🧭 I begin dynamically completing the quest...")

    quest_data = await fetch_active_quest_data()
    quest_targets = quest_data.get("targets", [])
    current_quest_id = quest_data["questId"]

    if not current_quest_id:
        return

    while True:
        quests_enable = await get_quest_enabled()
        if not quests_enable:
            print("🔴 Quest disabled in UI — I'm stopping the loop.")
            await disable_quest_hooks()
            break

        quest_data = await fetch_active_quest_data()
        quest_id = quest_data.get("questId")
        quest_targets = quest_data.get("targets", [])
        quest_items = quest_data.get("questItems", [])
        quest_title = quest_data.get("questTitle")

        if quest_title == "Początek drogi bohatera.":
            return

        map_2d = await current_location_map()
        start_position = await current_position()

        nearest_coords, path_to_nearest = await find_nearest_mob(
            map_2d, start_position, [(t["x"], t["y"]) for t in quest_targets]
        )

        if not nearest_coords:
            print("⚠️ No closest target found (no mobs or NPCs).")
            await asyncio.sleep(2)
            continue

        nearest_target = next(
            (t for t in quest_targets if (t["x"], t["y"]) == nearest_coords[0]), None
        )

        if nearest_target is None:
            print("⚠️ Unable to match the target to the nearest coordinates.")
            await asyncio.sleep(2)
            continue

        print(
            f"\n🎯 Nearest target: {nearest_target['name']} ({nearest_target['kind']}) @({nearest_target['x']},{nearest_target['y']})"
        )

        await execute_quest_target(map_2d, start_position, nearest_target)
        await asyncio.sleep(random.uniform(0.5, 1.0))


async def execute_quest_target(map_2d, start, target):
    kind = target["kind"].upper()
    goal = (target["x"], target["y"])
    driver = await MyDriver().get_driver()

    path = a_star(map_2d, start, goal)
    if not path or len(path) < 2:
        return

    try:
        mob_id, _ = await get_npc_id([goal])
        walkOver = await is_npc_walkover(goal)
    except Exception:
        mob_id = None
        walkOver = False

    hasRenewableNpc = await driver.evaluate(
        f"() => !!window.Engine?.npcs?.getRenewableNpcByPosition({goal[0]}, {goal[1]})",
        isolated_context=False,
    )

    hasGateway = await driver.evaluate(
        f"() => !!window.Engine?.map?.gateways?.getGtwAtPosition({goal[0]}, {goal[1]})",
        isolated_context=False,
    )

    if kind == "TALK" or kind == "COLLECT":
        if hasRenewableNpc or hasGateway or walkOver:
            # await go_to_target(path, mob_id, mobType="gateway")
            if hasRenewableNpc:
                await go_to_target(path, mob_id, mobType="gateway")
                await collect_item(goal)
            else:
                current_map = await get_current_map()
                await follow_path(path, current_map)
        else:
            await go_to_target(path, mob_id, mobType="quest")
            await asyncio.sleep(random.uniform(0.4, 0.65))
            await talk_with_npc(mob_id, [1])
            await asyncio.sleep(random.uniform(0.4, 0.65))

            driver = await MyDriver().get_driver()
            await _auto_fight_if_active(driver)

            barter_opened = await driver.evaluate(
                "(() => !!window.Engine?.barter)()", isolated_context=False
            )

            if barter_opened:
                print("⚙️ Open barter detected — item creation...")
                await create_item()
                await asyncio.sleep(random.uniform(0.8, 1.2))

            shop_items = await driver.evaluate(
                """
                (() => {
                    const shop = window.Engine?.shop?.getItems?.() || {};
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
                await handle_quest_items(
                    (await fetch_active_quest_data())["questItems"], shop_items
                )

            new_items = await driver.evaluate(
                """
                    (() => {
                        const items = window.Engine.items.fetchLocationItems("g");
                        return items
                            .filter(item => item.getNow === true || item._cachedStats?.lootbox)
                            .filter(item => item.itemClType !== 15)
                            .filter(item => !item._cachedStats?.bag)
                            .filter(item => {
                                const type = item.getReqpStat();
                                const lvl = item.getLvlStat();
                                const hasRecipe = item._cachedStats?.recipe;
                                return type || lvl || hasRecipe;
                            })
                            .map(item => ({
                                id: item.id,
                                lvl: item.getLvlStat(),
                                hasRecipe: !!item._cachedStats?.recipe,
                                isLootbox: !!item._cachedStats?.lootbox,
                            }));
                    })();
                """,
                isolated_context=False,
            )

            if new_items:
                recipes = [i for i in new_items if i["hasRecipe"]]
                hero_lvl = await get_hero_lvl()
                equipables = [
                    i
                    for i in new_items
                    if (i["lvl"] is None or hero_lvl >= int(i["lvl"]))
                    # if not i["hasRecipe"] and (i["lvl"] is None or hero_lvl >= int(i["lvl"]))
                ]

                if equipables:
                    print(f"🧥 New items to equip: {len(equipables)}")
                    await equip_item([i["id"] for i in equipables])

                    lootboxes = [
                        i
                        for i in new_items
                        if i.get("isLootbox") and hero_lvl >= int(i["lvl"])
                    ]
                    if lootboxes:
                        await accept_loot()

                if recipes:
                    await open_and_create_recipe()
                    await asyncio.sleep(random.uniform(0.8, 1.2))

    elif kind == "KILL":
        if hasRenewableNpc or hasGateway or walkOver:
            # await go_to_target(path, mob_id, mobType="gateway")
            current_map = await get_current_map()
            await follow_path(path, current_map)
        else:
            result = await go_to_target(path, mob_id, mobType="quest")
            print(result, mob_id, path, target["name"])
            if result:
                await attack_mob(mob_id, target["name"])

    await asyncio.sleep(random.uniform(0.8, 1.3))


async def handle_quest_items(quest_items, shop_items):
    if not quest_items:
        return

    items_to_buy = []

    for q_item_name in quest_items:
        for shop_item in shop_items:
            if shop_item["name"].lower() == q_item_name.lower():
                items_to_buy.append(shop_item["id"])

    if not items_to_buy:
        return

    await buy_item(items_to_buy, 1)


async def disable_quest_hooks():
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

            if (window.BotQuestTargets) window.BotQuestTargets = { KILL: [], TALK: null, COLLECT: null };
            console.log("%c🧹 Quest hooks deactivated and status cleared.", "color:orange;font-weight:bold;");
        })();
        """,
        isolated_context=False,
    )


async def disable_dialog_interceptor():
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


async def run_quest_service():
    await disable_quest_hooks()

    try:
        await inject_quest_observer()
        await inject_dialog_interceptor()
        print("✅ The quest observer has been activated.")

        while True:
            quests_enable = await get_quest_enabled()
            if not quests_enable:
                print("🔴 Quest disabled in UI — stopping the loop.")
                await disable_dialog_interceptor()
                await disable_quest_hooks()
                break

            quest_data = await fetch_active_quest_data()
            quest_id = quest_data.get("questId")
            quest_title = quest_data.get("questTitle")

            if quest_title == "Początek drogi bohatera.":
                await set_selected_exp_to_new_value("Mrówki")
                return

            if not quest_id:
                print("⚠️ No active quest — waiting for a new one...")
                await asyncio.sleep(1.5)
                continue

            print(f"🎯 Active quest detected: {quest_title} (ID: {quest_id})")
            await quest_service()

            await asyncio.sleep(random.uniform(0.5, 0.75))

    except Exception as e:
        print(f"❌ Error in run_quest_service: {e}")
