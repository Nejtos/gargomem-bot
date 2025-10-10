import asyncio
import random
from bot.core.driver import MyDriver


async def wait_for_page_load(current_map):
    while True:
        await asyncio.sleep(random.uniform(0.94, 1.29))
        new_map = await get_current_map()
        if new_map != current_map:
            print("Map has changed.")
            break


async def get_main_map_name():
    driver = await MyDriver().get_driver()
    main_map_name = await driver.evaluate(
        "() => window.Engine.map.d.name", isolated_context=False
    )
    return main_map_name


async def get_main_map_id():
    driver = await MyDriver().get_driver()
    main_map_id = await driver.evaluate(
        "() => window.Engine.map.d.mainid", isolated_context=False
    )
    return main_map_id


async def get_current_map():
    driver = await MyDriver().get_driver()
    map_id = await driver.evaluate(
        "() => window.Engine.map.d.id", isolated_context=False
    )
    return map_id


async def map_size():
    driver = await MyDriver().get_driver()
    map_sizeXY = await driver.evaluate(
        "() => [window.Engine.map.d.x, window.Engine.map.d.y]", isolated_context=False
    )
    return map_sizeXY


async def update_collisions():
    driver = await MyDriver().get_driver()
    script = """
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
    """
    collisions = await driver.evaluate(script, isolated_context=False)
    return collisions


async def get_gateways():
    driver = await MyDriver().get_driver()
    script = f"""
            (function() {{
                let gtwList = []
                gateway = window.Engine.map.gateways.getList().flat()
                for (var i = 0; i < gateway.length; i++) {{
                    var objectD = gateway[i]['d'];
                    gtwList = gtwList.concat(objectD);
                }}
                return gtwList
            }})();
        """
    gateways = await driver.evaluate(script, isolated_context=False)
    return gateways


async def get_gateway_pos(gateway, nextMapId):
    driver = await MyDriver().get_driver()
    script = f"""
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
        """
    gateway_pos = await driver.evaluate(script, isolated_context=False)
    return gateway_pos
