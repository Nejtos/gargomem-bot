import asyncio
import random
from bot.core.driver import MyDriver
from bot.integrations.dsc_loot_notifier import dsc_loot_msg, heroes_dsc_loot_msg


async def _is_mob_alive(driver, mobId):
    script = f"""
        () => {{
            let mob = window.Engine.npcs.getById('{mobId}');
            return mob !== undefined && mob !== null ? 1 : 0;
        }}
    """
    return await driver.evaluate(script, isolated_context=False) != 0


async def _auto_fight_if_active(driver):
    script = "(function(){return window.Engine.battle.isBattleShow();})();"
    active = await driver.evaluate(script, isolated_context=False)
    if active:
        await driver.evaluate(
            "() => window.Engine.battle.autoFight();", isolated_context=False
        )
    return active


async def attack_mob(mobId, mob_name, heroes=False, heal_event=None):
    driver = await MyDriver().get_driver()

    while await _is_mob_alive(driver, mobId):
        if await _auto_fight_if_active(driver):
            await asyncio.sleep(random.uniform(0.1, 0.2))
            continue
        script = f"""_g("fight&a=attack&ff=1&id=-{mobId}")"""
        # script = f"""() => window.Engine.hero.heroAtackRequest({mobId}, 1)"""
        await driver.evaluate(script, isolated_context=False)

        await asyncio.sleep(random.uniform(0.72, 1.09))

    if heal_event:
        heal_event.set()

    if heroes:
        await heroes_dsc_loot_msg(mob_name)
    else:
        await dsc_loot_msg(mob_name)
