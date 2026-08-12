from bot.game.entities.base import GameEntity


class Map(GameEntity):
    async def get_current_map_mainId(self) -> int:
        return await self._evaluate("() => window.Engine.map.d.mainid")

    async def get_current_map_id(self) -> int:
        return await self._evaluate("() => window.Engine.map.d.id")

    async def get_current_map_name(self) -> str:
        return await self._evaluate("() => window.Engine.map.d.name")

    async def get_current_map_size(self) -> list:
        return await self._evaluate(
            "() => [window.Engine.map.d.x, window.Engine.map.d.y]"
        )

    async def get_current_map_collisions(self) -> list:
        return await self._evaluate("""
            (function() {
                var a = [];
                var b = window.Engine.map.d.x;
                var c = window.Engine.map.d.y;

                for (var d = 0; d < c + 1; d++) {
                    for (var _c = 0; _c < b + 1; _c++) {
                        var value = window.Engine.map.col.check(_c, d);
                        if (value > 1) {
                            value = 1;
                        }
                        a.push(value);
                    }
                }
                return a.join("");
            })();
        """)

    async def get_current_map_gateways(self) -> list:
        return await self._evaluate(f"""
            (function() {{
                let gtwList = []
                gateway = window.Engine.map.gateways.getList().flat()
                for (var i = 0; i < gateway.length; i++) {{
                    var objectD = gateway[i]['d'];
                    gtwList = gtwList.concat(objectD);
                }}
                return gtwList
            }})();
        """)

    async def get_current_map_gateway_pos(self, gateway, nextMapId) -> list:
        return await self._evaluate(f"""
            (function(gateway, nextMapId) {{
                var gatewayPos = [];
                for (var object of gateway) {{
                    if (object.id === nextMapId) {{
                        gatewayPos.push(object.x);
                        gatewayPos.push(object.y);
                    }}
                }}
                return gatewayPos;
            }})({gateway}, {nextMapId});
        """)
