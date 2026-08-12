from bot.game.entities.base import GameEntity


class PlayerInventory(GameEntity):
    async def get_potions(self):
        return await self._evaluate("""(function() {
            let items = window.Engine.items.fetchLocationItems("g").filter(item => item._cachedStats.hasOwnProperty("leczy")).filter(item => item._cachedStats.leczy > 400);
            let ids = items.map(item => item.id);
            return ids;
        })();""")

    async def get_free_slots(self):
        return await self._evaluate("() => window.Engine.heroEquipment.getFreeSlots()")
