from bot.core.driver import MyDriver


async def get_npcs_from_NI():
    driver = await MyDriver().get_driver()
    script = """
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
    """
    npcs_from_NI = await driver.evaluate(script, isolated_context=False)
    return npcs_from_NI


async def is_in_proximity_via_path(path, threshold=3):
    return len(path) <= threshold
