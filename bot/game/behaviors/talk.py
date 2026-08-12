import asyncio
import random
from bot.game.entities.dialogue import Dialogue


async def talk_with_npc(mob_id, _options=None):
    dialogue = Dialogue()
    await dialogue.talk_with_npc(mob_id)
    for _ in range(20):
        if await dialogue.is_dialogue_open():
            break
        await asyncio.sleep(0.2)
    else:
        print("⚠️ talk_with_npc: dialog się nie otworzył, pomijam")
        return
    if _options is not None:
        while await dialogue.is_dialogue_open():
            await asyncio.sleep(random.uniform(0.2, 0.35))
            await dialogue.select_defined_dialogue_line(_options)
            await asyncio.sleep(random.uniform(0.55, 0.75))
