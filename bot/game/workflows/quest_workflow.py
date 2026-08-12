import asyncio
import random

from bot.game.entities.mob import Mob
from bot.game.entities.player import Player
from bot.game.services.map_services import current_location_map
from bot.game.services.mob_service import find_nearest_quest_mob
from bot.game.services.quest_service import (
    disable_all,
    disable_quest_hooks,
    execute_quest_target,
    fetch_active_quest_data,
    inject_dialog_interceptor,
    inject_quest_observer,
    is_quest_enabled,
)
from bot.ui.botUI import BotUI

INTRO_QUEST_TITLE = "Początek drogi bohatera."


async def run_quest_workflow() -> None:
    await disable_quest_hooks()

    try:
        await inject_quest_observer()
        await inject_dialog_interceptor()
        print("✅ The quest observer has been activated.")

        while True:
            if not await is_quest_enabled():
                print("🔴 Quest disabled in UI — stopping the loop.")
                await disable_all()
                break

            quest_data = await fetch_active_quest_data()
            quest_id = quest_data.get("questId")
            quest_title = quest_data.get("questTitle")

            if quest_title == INTRO_QUEST_TITLE:
                await BotUI().set_selected_exp_to_new_value("Mrówki")
                return

            if not quest_id:
                print("⚠️ No active quest — waiting for a new one...")
                await asyncio.sleep(1.5)
                continue

            print(f"🎯 Active quest detected: {quest_title} (ID: {quest_id})")
            await farm_quest_targets()

            await asyncio.sleep(random.uniform(0.5, 0.75))

    except Exception as e:
        print(f"❌ Error in run_quest_workflow: {e}")


async def farm_quest_targets() -> None:
    print("🧭 I begin dynamically completing the quest...")

    quest_data = await fetch_active_quest_data()
    if not quest_data["questId"]:
        return

    player = Player()

    while True:
        if not await is_quest_enabled():
            print("🔴 Quest disabled in UI — I'm stopping the loop.")
            await disable_all()
            break

        quest_data = await fetch_active_quest_data()
        raw_targets = quest_data.get("targets", [])
        quest_title = quest_data.get("questTitle")

        if quest_title == INTRO_QUEST_TITLE:
            return

        if not raw_targets:
            print("⚠️ No quest targets found.")
            await asyncio.sleep(2)
            continue

        # quest_mobs = [
        #     Mob(
        #         id="",
        #         name=t.get("name", "Target"),
        #         position=(t["x"], t["y"]),
        #         kind=t.get("kind", "UNKNOWN"),
        #     )
        #     for t in raw_targets if t
        # ]
        target_kinds = {
            (t["x"], t["y"]): t.get("kind", "UNKNOWN") for t in raw_targets if t
        }
        quest_mobs = [
            Mob(name=t.get("name", "Target"), position=(t["x"], t["y"]))
            for t in raw_targets if t
        ]

        map_2d = await current_location_map()
        start_position = await player.position()

        target_mob, path = await find_nearest_quest_mob(map_2d, start_position, quest_mobs)

        if not target_mob or not path:
            print("⚠️ No closest target found (no mobs or NPCs).")
            await asyncio.sleep(2)
            continue

        # print(f"\n🎯 Nearest target: {target_mob.name} ({target_mob.kind}) @{target_mob.position}")

        # aborted = await execute_quest_target(map_2d, start_position, target_mob)
        kind = target_kinds.get(target_mob.position, "UNKNOWN")
        print(f"\n🎯 Nearest target: {target_mob.name} ({kind}) @{target_mob.position}")

        aborted = await execute_quest_target(map_2d, start_position, target_mob, kind)
        if aborted:
            print("🔴 Quest disabled in UI mid-action — stopping the loop.")
            await disable_all()
            break

        await asyncio.sleep(random.uniform(0.5, 1.0))