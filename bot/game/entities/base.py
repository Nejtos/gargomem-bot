from bot.core.driver import MyDriver


class GameEntity:
    async def _driver(self):
        return await MyDriver().get_driver()

    async def _evaluate(self, script: str):
        driver = await self._driver()
        return await driver.evaluate(script, isolated_context=False)