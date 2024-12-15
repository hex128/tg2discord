#!/usr/bin/env python3
import json
import os

import aiohttp
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.events import NewMessage

load_dotenv()

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
session_name = os.environ.get("TELEGRAM_SESSION_NAME", "tg2discord")
mapping_json_path = os.environ.get("MAPPING_JSON_PATH", os.path.join(os.path.dirname(__file__), "mapping.json"))

client = TelegramClient(session_name, api_id, api_hash)

with open(mapping_json_path, 'r') as mapping_json_file:
    mapping = json.load(mapping_json_file)


async def send_to_discord(url, message):
    print(f"Sending {message} to {url}")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        for attempt in range(3):
            try:
                async with session.post(f"{url}?wait=true", json={"content": message}) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise


async def channel_handler(event):
    channel_username = (await event.client.get_entity(event.chat_id)).username
    message = event.message.message
    if not channel_username.startswith("@"):
        channel_username = f"@{channel_username}"
    print(f"New message from {channel_username}: {message}")

    for webhook_url in mapping.get(channel_username, []):
        resp = await send_to_discord(webhook_url, message)
        print(resp)


async def main():
    print(f"Monitoring sensor channels {','.join(mapping.keys())}")
    client.add_event_handler(channel_handler, NewMessage(chats=set(mapping.keys())))
    await client.start()
    print("Monitoring messages...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
