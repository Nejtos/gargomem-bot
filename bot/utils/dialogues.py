import asyncio
import random
from bot.core.driver import MyDriver


async def is_dialogue_open():
    driver = await MyDriver().get_driver()
    script = """
        () => {
            let isOpen = document.querySelector('.dialogue-window.is-open')
            return isOpen
        }
    """
    isOpen = await driver.evaluate(script, isolated_context=False)
    if isOpen:
        return True
    else:
        return False


async def select_first_dialogue_line():
    driver = await MyDriver().get_driver()
    script = """() => window.Engine.dialogue.hotKeyLine('1')"""
    await driver.evaluate(script, isolated_context=False)


async def select_dialogue_line(options):
    driver = await MyDriver().get_driver()
    for i in range(len(options)):
        key = options[i]
        script = f"""() => window.Engine.dialogue.hotKeyLine('{key}')"""
        await driver.evaluate(script, isolated_context=False)
        await asyncio.sleep(random.uniform(0.24, 0.32))


async def talk_with_npc(mob_id, _options=None):
    driver = await MyDriver().get_driver()
    script = f"""(() => _g("talk&id={mob_id}"))()"""
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.1, 0.2))
    while await is_dialogue_open():
        await asyncio.sleep(random.uniform(0.15, 0.25))
