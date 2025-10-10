import asyncio
import os
import time
import random
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from bot.core.driver import MyDriver
from bot.utils.helpers import accept_loot


load_dotenv()


async def dsc_loot_msg(mob_name):
    driver = await MyDriver().get_driver()
    msg_to_sent = []
    script = f"""
        (function() {{
            let txt = "";
            let items = window.Engine.items.fetchLocationItems("l");
            if (items.length !== 0) {{
                let itemType = items[0]._cachedStats?.rarity;
                if (itemType && itemType !== "common") {{
                    txt = "{mob_name}: zdobyto " + items[0].name + " [" + items[0].itemTypeName + "]";
                    return txt;
                }}
            }}
            else {{
                return txt;
            }}
        }})();
    """
    msg_text = await driver.evaluate(script, isolated_context=False)
    msg_to_sent.append(msg_text)

    if msg_to_sent and msg_to_sent[0] != "":
        await asyncio.sleep(random.uniform(0.1, 0.25))
        await accept_loot()

    if len(msg_to_sent) != 0 and msg_to_sent[-1] != "" and msg_to_sent[-1] is not None:
        print("MSG:", str(msg_to_sent[-1]))
        data = {"content": str(msg_to_sent[-1])}

        discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        response = requests.post(
            discord_webhook_url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 204:
            print("Data was successfully sent to the Discord channel.")
        else:
            print("There was a problem sending data to the Discord channel.")


async def heroes_dsc_loot_msg(mob_name):
    driver = await MyDriver().get_driver()
    msg_to_sent = []
    script = f"""
        (function() {{
            let txt = "";
            let items = window.Engine.items.fetchLocationItems("l");
            if (items.length !== 0) {{
                let itemType = items[0]._cachedStats?.rarity;
                if (itemType) {{
                    txt = "{mob_name}: zdobyto " + items[0].name + " [" + items[0].itemTypeName + "]";
                    return txt;
                }}
            }}
            else {{
                return txt;
            }}
        }})();
    """
    msg_text = await driver.evaluate(script, isolated_context=False)
    msg_to_sent.append(msg_text)

    if msg_to_sent and msg_to_sent[0] != "":
        await asyncio.sleep(random.uniform(0.1, 0.25))
        await accept_loot()

    if len(msg_to_sent) != 0 and msg_to_sent[-1] != "" and msg_to_sent[-1] is not None:
        print("MSG:", str(msg_to_sent[-1]))
        data = {"content": str(msg_to_sent[-1])}

        discord_webhook_url = os.getenv("DISCORD_WEBHOOK_HEROES_URL")

        response = requests.post(
            discord_webhook_url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 204:
            print("Data was successfully sent to the Discord channel.")
        else:
            print("There was a problem sending data to the Discord channel.")
