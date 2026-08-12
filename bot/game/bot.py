import asyncio
import random
import sys
import traceback

import keyboard

from bot.core.driver import MyDriver
from bot.core.movement_guard import is_move_blocked
from bot.core.captcha import is_captcha_active
from bot.game.entities.player import Player
from bot.game.services.helpers import get_respawn_time, retry
from bot.game.workflows.exp_workflow import run_exp_workflow
from bot.game.services.heroes.heroes_service import heroes_service
from bot.game.services.quest_service import disable_quest_hooks
from bot.game.workflows.quest_workflow import run_quest_workflow
from bot.game.workflows.e2_workflow import run_e2_workflow
from bot.ui.botUI import BotUI, BotUISelections
import bot.globals as globals


class GameBot:
    def __init__(self, heal_event: asyncio.Event, captcha_event: asyncio.Event) -> None:
        self._heal_event = heal_event
        self._captcha_event = captcha_event
        self._driver = MyDriver()
        self._ui = BotUI()
        self._quests_enabled = False

    async def run(self) -> None:
        prof_index = await self._driver.get_profNum()
        print(f"Bot is running - profile {prof_index}")
        globals.is_game_loading[0] = True

        try:
            while True:
                if keyboard.is_pressed("|"):
                    print("🛑 Stop key detected — shutting down...")
                    break
                await self._handle_game_flow()
                await asyncio.sleep(0.1)
        except Exception as e:
            print("⚠️ BOT CRASH DETECTED ⚠️")
            traceback.print_exc()
            print(f"❌ Error message: {e}")
            await asyncio.sleep(3)
        finally:
            print("🛑 Bot has stopped — closing browser...")
            try:
                await self._driver.close_driver()
            finally:
                sys.exit(0)

    @retry(max_attempts=10, delay=5, refresh=True)
    async def _handle_game_flow(self) -> None:
        player = Player()
        captcha_active = await self._check_captcha_and_loading()

        if await player.is_dead():
            respawn_time = await get_respawn_time()
            print(f"💀 Character is unconscious — waiting {respawn_time} seconds to respawn...")
            await asyncio.sleep(respawn_time + 2)
            self._heal_event.set()

        selections: BotUISelections = await self._ui.get_selections()
        await self._sync_quest_state(selections.quest_enabled)

        if selections.selected_exp and selections.selected_exp != "Wybierz":
            await self._handle_exp_selection(selections.selected_exp, selections.selected_e2)
        elif selections.selected_e2 and selections.selected_e2 != "Wybierz" and not captcha_active:
            await run_e2_workflow(self._heal_event, None, selections.selected_e2)
        elif selections.selected_heroes and selections.selected_heroes != "Wybierz":
            await heroes_service(selections.selected_heroes, self._heal_event)

    async def _sync_quest_state(self, quests_enabled: bool) -> None:
        if quests_enabled and not self._quests_enabled:
            await run_quest_workflow()
            await self._quest_service.run()
            self._quests_enabled = True
        elif not quests_enabled and self._quests_enabled:
            await disable_quest_hooks()
            self._quests_enabled = False

    async def _check_captcha_and_loading(self) -> bool:
        captcha_active = await is_captcha_active()

        if globals.is_game_loading[0] and captcha_active:
            self._captcha_event.set()
            await self._captcha_event.wait()
            await asyncio.sleep(random.uniform(2.0, 4.0))
        else:
            globals.is_game_loading[0] = False
            await is_move_blocked(self._captcha_event)

        return captcha_active

    async def _handle_exp_selection(self, selected_exp: str, selected_e2: str | None) -> None:
        if selected_e2 and selected_e2 != "Wybierz":
            return
        await run_exp_workflow(self._heal_event, selected_exp, self._ui)
