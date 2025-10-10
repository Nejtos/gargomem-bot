from functools import reduce


from bot.game.interactions.attack import attack_mob
from bot.game.moving.moving import create_path, go_to_target
from bot.game.navigation.maps import go_to_gateway
from bot.utils.dialogues import talk_with_npc
from bot.utils.helpers import accept_loot, current_location_map
from bot.utils.items import (
    equip_item,
    buy_item,
    collect_item,
    open_and_create_recipe,
    create_item,
    get_item_id_by_name,
)


from bot.game.tutorials.items_dict import (
    getRightItems,
)
from bot.ui.botUI import set_selected_exp_to_default


npcs_id = [
    "178339",
    "178362",
    "178365",
    "178370",
    "181266",
    "178389",
    "189492",
    "189809",
    "178488",
    "181471",
    "162040",
    "191235",
    "175174",
    "160885",
    "181123",
    "21946",
    "254615",
    "21977",
    "146657",
]
npcs_name = [
    ["Pająk piwniczak"],
    ["Młody gaunt jaskiniowy"],
    ["Sieciarz jaskiniowy", "Kolczak zbrojny"],
    ["Wściekły pies"],
    ["Szary wilk", "Agresywna Czarna Wilczyca"],
    ["Nieumarły wojownik", "Nieumarły mnich", "Nieumarły wiarus"],
    ["Czarnoksiężnik Astratus"],
    ["Puma"],
    ["Ranna Mushita"],
]
items_to_buy = [
    ["34279"],
    ["141", "25571", "34019", "83", "66"],
    ["25573", "22916", "22917", "10358", "10354", "31922"],
]
recipes_id = [595, 1616, 1631, 596, 2301]
dialogue_options = [[], [2, 1, 1], [2, 1, 1, 1, 1, 1], [2, 1], [2, 1, 1, 1, 1, 1, 1]]
collectable_items_pos = [
    (7, 10),
    (94, 31),
    (83, 38),
]
gateways_pos = [
    (7, 20),
    (54, 16),
    (9, 16),
    (45, 6),
    (17, 30),
    (11, 27),
    (3, 14),
    (0, 31),
    (34, 46),
    (26, 24),
    (0, 34),
    (59, 18),
    (21, 6),
    (34, 19),
    (3, 7),
    (3, 3),
    (11, 14),
    (18, 10),
    (95, 34),
    (33, 37),
    (48, 0),
    (10, 48),
]


async def go_and_talk(mob_name, npc_id, options):
    locMap = await current_location_map()
    path = await create_path(mob_name, locMap)
    await go_to_target(path, npc_id)
    await talk_with_npc(npc_id, options)


async def find_item_and_equip(items_name_arr):
    items = []
    for i in range(len(items_name_arr)):
        items.append(await get_item_id_by_name(items_name_arr[i]))
    items = reduce(lambda a, b: a + b, items)
    await equip_item(items, len(items))


async def tutorial_part1():
    # Pomieszczenie startowe
    itemsName = await getRightItems()
    await go_and_talk("Szabrownik Renard", npcs_id[0], dialogue_options[0])
    await find_item_and_equip(itemsName[0])
    await talk_with_npc(npcs_id[0], dialogue_options[0])
    await attack_mob(npcs_name[0])
    await go_and_talk("Szabrownik Renard", npcs_id[0], dialogue_options[0])
    await go_to_gateway(gateways_pos[0])
    await set_selected_exp_to_default()


async def tutorial_part2():
    # Ruiny Szabrowników
    itemsName = await getRightItems()
    await go_and_talk("Szabrowniczka Anisja", npcs_id[1], dialogue_options[0])
    await go_and_talk("Mag Meliorn", npcs_id[2], dialogue_options[0])
    await go_and_talk("Kości", npcs_id[3], dialogue_options[0])
    await go_and_talk("Mag Meliorn", npcs_id[2], dialogue_options[0])
    await find_item_and_equip(itemsName[1])
    await accept_loot()
    await go_and_talk("Szabrownik Sergiusz", npcs_id[4], dialogue_options[0])
    await go_and_talk("Szabrownik Garret", npcs_id[5], dialogue_options[0])
    await find_item_and_equip(itemsName[2])
    await go_to_gateway(gateways_pos[1])
    await attack_mob(npcs_name[1])
    await go_and_talk("Martwy szabrownik", npcs_id[6], dialogue_options[0])
    await go_to_gateway(gateways_pos[2])
    await go_and_talk("Szabrownik Garret", npcs_id[5], dialogue_options[0])
    await go_and_talk("Zielarka Flarenia", npcs_id[7], dialogue_options[0])
    await buy_item(items_to_buy[0], len(items_to_buy[0]))
    await go_and_talk("Szabrownik Garret", npcs_id[5], dialogue_options[0])
    await go_and_talk("Handlarz Erwin", npcs_id[8], dialogue_options[0])
    await find_item_and_equip(itemsName[3])
    await go_to_gateway(gateways_pos[3])
    await attack_mob(npcs_name[2])
    await go_to_gateway(gateways_pos[4])
    await go_and_talk("Handlarz Erwin", npcs_id[8], dialogue_options[0])
    await buy_item(items_to_buy[1], len(items_to_buy[1]))
    await find_item_and_equip(itemsName[4])
    await go_and_talk("Szabrownik Jack", npcs_id[9], dialogue_options[0])
    await go_and_talk("Alchemik Mirvas", npcs_id[10], dialogue_options[0])
    await go_to_gateway(gateways_pos[-1])
    await attack_mob(npcs_name[3])
    await go_to_gateway(gateways_pos[5])
    await collect_item(collectable_items_pos[0])
    await go_to_gateway(gateways_pos[6])
    await go_and_talk("Alchemik Mirvas", npcs_id[10], dialogue_options[0])
    await find_item_and_equip(itemsName[5])
    await open_and_create_recipe(recipes_id[0])
    await find_item_and_equip(itemsName[6])
    await go_and_talk("Alchemik Mirvas", npcs_id[10], dialogue_options[0])
    await go_to_gateway(gateways_pos[7])
    await set_selected_exp_to_default()


async def tutorial_part3():
    # Zatopione Szczyty
    itemsName = await getRightItems()
    await go_and_talk("Ernest", npcs_id[11], dialogue_options[0])
    await go_and_talk("Stary Fonso", npcs_id[12], dialogue_options[0])
    await create_item(0, recipes_id[1])
    await go_and_talk("Stary Fonso", npcs_id[12], dialogue_options[0])
    await go_and_talk("Ernest", npcs_id[11], dialogue_options[0])
    await buy_item(items_to_buy[2], len(items_to_buy[2]))
    await find_item_and_equip(itemsName[7])
    await go_to_gateway(gateways_pos[8])
    await attack_mob(npcs_name[4])
    await go_to_gateway(gateways_pos[9])
    await go_and_talk("Stary Fonso", npcs_id[12], dialogue_options[0])
    await create_item(3, recipes_id[2])
    await go_and_talk("Vasylis", npcs_id[13], dialogue_options[0])
    await go_to_gateway(gateways_pos[10])
    await set_selected_exp_to_default()


async def tutorial_part4():
    # Stare Ruiny
    itemsName = await getRightItems()
    await go_and_talk("Victor", npcs_id[14], dialogue_options[0])
    await collect_item(collectable_items_pos[1])
    await collect_item(collectable_items_pos[2])
    await go_and_talk("Victor", npcs_id[14], dialogue_options[1])
    await find_item_and_equip(itemsName[8])
    await open_and_create_recipe(recipes_id[3])
    await go_and_talk("Victor", npcs_id[14], dialogue_options[1])
    await find_item_and_equip(itemsName[9])
    await go_to_gateway(gateways_pos[11])
    await go_to_gateway(gateways_pos[12])
    await attack_mob(npcs_name[5])
    await go_to_gateway(gateways_pos[13])
    await go_to_gateway(gateways_pos[14])
    await go_to_gateway(gateways_pos[15])
    await attack_mob(npcs_name[6])
    await go_to_gateway(gateways_pos[16])
    await go_to_gateway(gateways_pos[17])
    await go_and_talk("Victor", npcs_id[14], dialogue_options[2])
    await go_to_gateway(gateways_pos[18])
    await go_and_talk("Gosza", npcs_id[15], dialogue_options[0])
    await attack_mob(npcs_name[7])
    await go_and_talk("Honza", npcs_id[16], dialogue_options[0])
    await attack_mob(npcs_name[8])
    await go_to_gateway(gateways_pos[19])
    await go_and_talk("Honza", npcs_id[16], dialogue_options[0])
    await go_and_talk("Aza", npcs_id[17], dialogue_options[3])
    await go_to_gateway(gateways_pos[10])
    await go_and_talk("Victor", npcs_id[14], dialogue_options[1])
    await create_item(0, recipes_id[4])
    await go_and_talk("Victor", npcs_id[14], dialogue_options[0])
    await go_and_talk("Domina Ecclesiae", npcs_id[18], dialogue_options[0])
    await go_to_gateway(gateways_pos[14])
    await go_and_talk("Victor", npcs_id[14], dialogue_options[4])
    await go_to_gateway(gateways_pos[20])
    await find_item_and_equip(itemsName[10])
    await set_selected_exp_to_default()
