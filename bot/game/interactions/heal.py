import asyncio
from bot.core.driver import MyDriver


async def hp_stats():
    driver = await MyDriver().get_driver()
    script = """
        (function() {
            let maxHp = window.Engine.hero.d.warrior_stats.maxhp;
            let hp = window.Engine.hero.d.hp;
            let hp_stat = window.Engine.hero.d.warrior_stats.hp;
            return [maxHp, hp, hp_stat];
        })();
    """
    stats = await driver.evaluate(script, isolated_context=False)
    return stats


async def get_potions():
    driver = await MyDriver().get_driver()
    script = """
        (function() {
            let items = window.Engine.items.fetchLocationItems("g").filter(item => item._cachedStats.hasOwnProperty("leczy")).filter(item => item._cachedStats.leczy > 400);
            let ids = items.map(item => item.id);
            return ids;
        })();
    """
    potions = await driver.evaluate(script, isolated_context=False)
    return potions


async def have_potions(potions):
    return bool(potions)


async def potions_amount(potions):
    return len(potions)


async def heal_hero(heal_event):
    driver = await MyDriver().get_driver()
    hp_info_list = await hp_stats()
    max_hp, hp, hp_stat = hp_info_list
    if hp is not None and hp < 0.8 * max_hp:
        hp_stat = hp
        while hp_stat < 0.92 * max_hp:
            potions = await get_potions()
            if not await have_potions(potions):
                return
            potion_id = potions[-1]
            script = f"""(function() {{ _g("moveitem&st=1&id={potion_id}")}})();"""
            await driver.evaluate(script, isolated_context=False)
            await asyncio.sleep(0.2)
            hp_info_list = await hp_stats()
            hp_stat = hp_info_list[2]
    heal_event.clear()
