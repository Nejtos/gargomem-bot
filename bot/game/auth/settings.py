import random
import asyncio
from bot.core.driver import MyDriver


async def settings():
    driver = await MyDriver().get_driver()

    await driver.evaluate("() => window.Engine.settings.open()", isolated_context=False)
    await asyncio.sleep(random.uniform(0.5, 0.75))
    await driver.locator('li[data-serveroption="27"] .c-checkbox__label').click()
    await asyncio.sleep(random.uniform(0.5, 0.75))
    await driver.evaluate("() => window.Engine.settings.close()", isolated_context=False)
    await asyncio.sleep(random.uniform(0.7, 0.9))


async def addons():
    driver = await MyDriver().get_driver()

    await driver.evaluate(
        "() => Engine.addonsPanel.manageVisible()", isolated_context=False
    )
    await asyncio.sleep(random.uniform(0.7, 0.9))
    await driver.evaluate(
        "() => Engine.addonsPanel.manageVisible()", isolated_context=False
    )
