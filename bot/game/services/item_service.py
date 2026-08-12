def select_potion(hero_lvl, potions_dict):
    available = [p for p in potions_dict if hero_lvl <= p["max_lvl"]]
    if not available:
        return None

    selected = min(available, key=lambda x: x["max_lvl"])
    return selected["potion_id"]

# async def get_item_id_by_name(item_name):
#     driver = await MyDriver().get_driver()
#     script = f"""
#     () => {{
#         item = window.Engine.items.fetchLocationItems("g").filter(item => item.name === '{item_name}');
#         let id = item.map(x => x.id);
#         return id;
#     }}
#     """
#     item_id = await driver.evaluate(script, isolated_context=False)
#     return item_id


# async def filter_items_for_sale():
#     driver = await MyDriver().get_driver()
#     script = """
#         () => {
#             items = window.Engine.items
#                 .fetchLocationItems("g")
#                 .filter((item) =>
#                     item._cachedStats.hasOwnProperty("rarity") &&
#                     item._cachedStats.rarity === "common",
#                 )
#                 .filter((item) =>
#                     (!item._cachedStats.hasOwnProperty("leczy") ||
#                     item._cachedStats.leczy < 500) &&
#                     (!item._cachedStats.hasOwnProperty("teleport") ||
#                     item._cachedStats.teleport === ""),
#                 )
#                 .filter((item) =>
#                     item._cachedStats.hasOwnProperty("lvl") &&
#                     parseInt(item._cachedStats.lvl, 4) < 30,
#                 )
#                 .filter((item) =>
#                     !item._cachedStats.hasOwnProperty("bag") ||
#                     parseInt(item._cachedStats.bag, 4) < 1,
#                 );

#             let x = items;
#             eqItems = window.Engine.heroEquipment.getEqItems();
#             let y = Object.values(eqItems);
#             let filteredItems = x.filter((item) => !y.includes(item));
#             return filteredItems
#         }
#     """
#     filtered_items = await driver.evaluate(script, isolated_context=False)
#     return filtered_items