import os
import json
import asyncio
import requests
import discord
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_HEROES_URL")

_client: Optional[discord.Client] = None
_ready_evt = asyncio.Event()
_waiters = {}

EMOJI_TO_DECISION = {"⚔️": "attack", "⏳": "wait", "🚪": "logout"}


class _ReactionWaiter:
    def __init__(
        self,
        message_id: int,
        channel_id: int,
        allowed_user_id: Optional[int],
        timeout: float,
    ):
        self.message_id = message_id
        self.channel_id = channel_id
        self.allowed_user_id = allowed_user_id
        self.future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        self.timeout = timeout


async def ensure_discord_client() -> discord.Client:
    global _client
    if _client and _client.is_ready():
        return _client
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN not found in environment (required for reactions).")

    intents = discord.Intents.default()
    intents.reactions = True
    intents.guild_messages = True
    intents.guilds = True

    _client = discord.Client(intents=intents)

    @_client.event
    async def on_ready():
        print(f"[DC] Logged in as {_client.user} (id: {_client.user.id})")
        _ready_evt.set()

    @_client.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if payload.user_id == _client.user.id:
            return
        waiter = _waiters.get(payload.message_id)
        if not waiter:
            return
        if waiter.allowed_user_id and payload.user_id != waiter.allowed_user_id:
            return
        emoji = payload.emoji.name
        decision = EMOJI_TO_DECISION.get(emoji)
        if decision and not waiter.future.done():
            waiter.future.set_result(decision)

    asyncio.create_task(_client.start(DISCORD_BOT_TOKEN))
    await _ready_evt.wait()
    return _client


async def start_discord_bot(presence_text: str = "Nasłuchuję…"):
    client = await ensure_discord_client()
    try:
        await client.change_presence(
            status=discord.Status.online, activity=discord.Game(name=presence_text)
        )
    except Exception:
        pass


async def request_hero_decision_via_webhook(
    hero_name: str,
    map_id: str,
    coords: tuple[int, int],
    allowed_user_id: Optional[int] = None,
    timeout: float = 20.0,  # decistion time (20 s)
    default_action: str = "attack",  # default action (attack)
    wait_seconds: float = 90.0,  # waiting time (90 s)
) -> str:
    if not DISCORD_WEBHOOK_URL:
        return default_action

    x, y = coords
    content = (
        f"👑 **Znaleziono herosa: {hero_name}** 👑\n"
        f"Na mapie: {map_id} - ({x}, {y})\n"
        f"Polecenia: ⚔️ = Atakuj, ⏳ = Czekaj ({int(wait_seconds)}s), 🚪 = Wyloguj\n"
        f"Na decyzję masz {int(timeout)}s. Po tym czasie automatycznie wykonam atak 🤺"
    )

    url = DISCORD_WEBHOOK_URL + (
        "&wait=true" if "?" in DISCORD_WEBHOOK_URL else "?wait=true"
    )
    try:
        resp = requests.post(
            url,
            data=json.dumps({"content": content}),
            headers={"Content-Type": "application/json"},
        )
    except Exception:
        return default_action

    if resp.status_code not in (200, 204):
        return default_action

    try:
        msg = resp.json()
        message_id = int(msg["id"])
        channel_id = int(msg["channel_id"])
    except Exception:
        return default_action

    try:
        client = await ensure_discord_client()
        channel = client.get_channel(channel_id) or await client.fetch_channel(
            channel_id
        )
        message = await channel.fetch_message(message_id)
        for e in ("⚔️", "⏳", "🚪"):
            try:
                await message.add_reaction(e)
            except Exception:
                pass
    except Exception:
        return default_action

    waiter = _ReactionWaiter(message_id, channel_id, allowed_user_id, timeout)
    _waiters[message_id] = waiter
    try:
        decision = await asyncio.wait_for(waiter.future, timeout=timeout)
        return decision
    except asyncio.TimeoutError:
        return default_action
    finally:
        _waiters.pop(message_id, None)
