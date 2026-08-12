from bot.game.entities.base import GameEntity


class PlayerInteractions(GameEntity):
    async def is_fight_active(self):
        return await self._evaluate(
            "(function(){return window.Engine.battle.isBattleShow();})();"
        )

    async def set_auto_fight(self):
        return await self._evaluate("() => window.Engine.battle.autoFight();")

    async def request_hero_attack(self, mob_id):
        return await self._evaluate(
            f"""() => window.Engine.hero.heroAtackRequest({mob_id}, 1)"""
        )

    async def move_hero(self, resultX, resultY):
        script = f"""
            () => window.Engine.hero.searchPath({{
                x: {resultX},
                y: {resultY}
            }}, !1);
        """
        return await self._evaluate(script)

    async def accept_loot(self) -> None:
        return await self._evaluate("() => window.Engine.loots.acceptLoot()")
