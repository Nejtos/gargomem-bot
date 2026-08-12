import asyncio
import random

from bot.game.entities.base import GameEntity


class Dialogue(GameEntity):
    async def is_dialogue_open(self) -> bool:
        return await self._evaluate("""
            () => !!document.querySelector('.dialogue-window.is-open')
        """)


    async def select_first_dialogue_line(self):
        return await self._evaluate("() => window.Engine.dialogue.hotKeyLine(1)")


    async def select_defined_dialogue_line(self, options: list[int]) -> None:
        for key in options:
            await self._evaluate(f"""() => window.Engine.dialogue.hotKeyLine({key})""")
            await asyncio.sleep(random.uniform(0.24, 0.32))

    async def talk_with_npc(self, mob_id):
        return await self._evaluate(f"""(() => _g("talk&id={mob_id}"))()""")
