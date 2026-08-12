from dataclasses import dataclass

from bot.game.entities.base import GameEntity


@dataclass
class Mob(GameEntity):
    """Reprezentuje potwora znalezionego w bieżącej iteracji pętli.

    Celowo bez cache'owania stanu poza tym co przyszło z jednego odczytu
    (id/name/position/lvl/type) - tworzony na nowo co pętlę.
    """
    id: str = ""
    name: str = ""
    position: tuple[int, int] = (0, 0)
    lvl: int = 0
    type: int = 0

    async def get_all_npcs(self) -> dict:
        return await self._evaluate("""
            (function() {
                function _arrayWithHoles(arr) {
                    if (Array.isArray(arr)) return arr;
                }

                function _slicedToArray(arr, i) {
                    return (_arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _nonIterableRest());
                }

                var a = window.Engine.npcs.check(),
                b = {};
                var npcsArr = Object.entries(a);

                for (var i = 0; i < npcsArr.length; i++) {
                    var tmpArr = _slicedToArray(npcsArr[i], 2),
                    c = tmpArr[0],
                    d = tmpArr[1];

                    b[c] = d.d;
                }
                return b;
            })();
        """)

    async def get_selected_npc_data(
        self,
        *,
        name: str | None = None,
        position: tuple[int, int] | None = None,
    ) -> list[dict]:
        """Zwraca pełne dane NPC/moba z bieżącej iteracji, filtrowane po nicku i/lub pozycji.

        Bez filtrów zwraca wszystkie NPC-e widoczne w danym momencie.
        """
        all_npcs = await self.get_all_npcs()

        result = []
        for npc_data in all_npcs.values():
            if name is not None and npc_data["nick"] != name:
                continue
            if position is not None and (npc_data["x"], npc_data["y"]) != position:
                continue
            result.append(npc_data)

        return result

    @classmethod
    def from_raw(cls, data: dict) -> "Mob":
        return cls(
            id=str(data["id"]),
            name=data["nick"],
            position=(data["x"], data["y"]),
            lvl=data["lvl"],
            type=data["type"],
        )

    async def is_mob_alive(self) -> bool:
        script = f"""
            () => {{
                let mob = window.Engine.npcs.getById('{self.id}');
                return mob !== undefined && mob !== null ? 1 : 0;
            }}
        """
        return await self._evaluate(script) != 0