async def find_mobs(selected_exp, mobs):
    if selected_exp in mobs:
        return mobs[selected_exp]
    else:
        return []


async def find_e2mob(selected_e2, e2mob_dict):
    if selected_e2 in e2mob_dict:
        return e2mob_dict[selected_e2]["mob_name"]
    else:
        return []
