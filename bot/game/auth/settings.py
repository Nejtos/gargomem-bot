import random
import asyncio
from bot.core.driver import MyDriver


async def settings():
    page = await MyDriver().get_driver()

    await page.evaluate("() => window.Engine.settings.open()")
    await asyncio.sleep(random.uniform(0.5, 0.75))
    await page.locator('li[data-serveroption="27"] .checkbox').click()
    await asyncio.sleep(random.uniform(0.5, 0.75))
    await page.click(
        'xpath=//div[contains(@class, "button green small") and .//div[contains(@class, "label") and text()="Zapisz"]]'
    )
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
