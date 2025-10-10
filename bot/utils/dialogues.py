import time, random
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
        time.sleep(random.uniform(0.23, 0.31))


async def talk_with_npc(mobId, options):
    driver = await MyDriver().get_driver()
    script = f"""() => _g("talk&id={mobId}")"""
    await driver.evaluate(script, isolated_context=False)
    time.sleep(random.uniform(0.41, 0.64))
    while await is_dialogue_open():
        if len(options) == 0:
            await select_first_dialogue_line()
        else:
            await select_dialogue_line(options)
        time.sleep(random.uniform(0.47, 0.65))
