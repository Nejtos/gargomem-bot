import random
import sys
import asyncio
from bot.utils.credentials import read_credentials
from bot.utils.threads import captcha_thread_func, heal_hero_thread_func
from bot.core.driver import MyDriver
from bot.game.auth.register import register
from bot.game.auth.login import login
from bot.ui.botUI import bot_interface
from bot.game.bot import bot
from bot.integrations.dsc_reaction_control import start_discord_bot
from dotenv import load_dotenv

load_dotenv()


async def main():
    await start_discord_bot("Stealth level: *undetectable* 😶‍🌫️")
    if len(sys.argv) < 2:
        print("Usage: python main.py <profile_number>")
        return

    prof_num = int(sys.argv[1])
    my_driver = MyDriver()
    await my_driver.init_driver(prof_num)

    heal_event = asyncio.Event()
    captcha_event = asyncio.Event()

    asyncio.create_task(heal_hero_thread_func(heal_event))
    asyncio.create_task(captcha_thread_func(captcha_event))

    creds = read_credentials()
    if prof_num in creds:
        await login(prof_num, creds)
    else:
        await register(prof_num)
    await asyncio.sleep(random.uniform(2.5, 5.5))
    await bot_interface()
    await bot(heal_event, captcha_event)


if __name__ == "__main__":
    asyncio.run(main())
