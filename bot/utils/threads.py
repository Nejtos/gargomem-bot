from bot.game.interactions.heal import heal_hero
from bot.core.captcha import captcha


async def captcha_thread_func(captcha_event):
    while True:
        await captcha_event.wait()
        await captcha(captcha_event)


async def heal_hero_thread_func(heal_event):
    while True:
        await heal_event.wait()
        await heal_hero(heal_event)
