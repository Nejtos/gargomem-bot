from bot.game.entities.base import GameEntity


class Player(GameEntity):
    async def prof(self) -> str:
        return await self._evaluate("() => window.Engine.hero.d.prof")

    async def lvl(self) -> int:
        return await self._evaluate("() => window.Engine.hero.d.lvl")

    async def is_dead(self) -> bool:
        return await self._evaluate("() => window.Engine.dead")
    
    async def position(self) -> tuple[int, int]:
        script = """
            (function() {
                return [window.Engine.hero.d.x, window.Engine.hero.d.y];
            })();
        """
        return await self._evaluate(script)

    async def hp_stats(self) -> tuple[int, int, int]:
        script = """
            (function() {
                let maxHp = window.Engine.hero.d.warrior_stats.maxhp;
                let hp = window.Engine.hero.d.hp;
                let hp_stat = window.Engine.hero.d.warrior_stats.hp;
                return [maxHp, hp, hp_stat];
            })();
        """
        return await self._evaluate(script)