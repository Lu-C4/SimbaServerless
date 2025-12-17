from char_skins import skins
import os
import random
import time
import zlib
import base64
import httpx
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("TOKEN")
CHANNEL_IDS = os.environ.get("CHANNEL_IDS").split(",")

DISCORD_API = "https://discord.com/api/v10"

ENCRYPT_KEY = os.environ.get("ENCRYPT_KEY")
KEY = bytes.fromhex(ENCRYPT_KEY)


def get_random_skin():
    return random.choice(skins)


def xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt(raw: str) -> str:
    compressed = zlib.compress(raw.encode(), level=9)
    encrypted = xor(compressed, KEY)
    return base64.b85encode(encrypted).decode()


import traceback

async def send_to_channel(client: httpx.AsyncClient, channel_id: str):
    try:
        skin = get_random_skin()
        image_url = f"https://ev.io{skin['field_large_thumb']}"

        headers = {
            "Authorization": f"Bot {BOT_TOKEN}",
        }

        payload = {
            "content": (
                "### A Stranded soldier has arrived!\n"
                f"||{encrypt(str(time.time()) + '$$' + skin['title'] + '$$' + skin['field_tier'])}||"
            ),
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 1,
                            "label": "Recruit!",
                            "custom_id": "recruit",
                        }
                    ],
                }
            ],
        }

        img_resp = await client.get(image_url)
        img_resp.raise_for_status()

        files = {
            "payload_json": (None, json.dumps(payload), "application/json"),
            "file": ("image.png", img_resp.content, "image/png"),
        }

        r = await client.post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            headers=headers,
            files=files,
        )

        r.raise_for_status()

        print(f"[✓] Sent to channel {channel_id}")

    except Exception as e:
        print(f"\n[✗] Channel {channel_id} failed")
        print(f"Type      : {type(e).__name__}")
        print(f"Repr      : {repr(e)}")
        print("Traceback:")
        traceback.print_exc()


async def sendSoldier():
    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [
            send_to_channel(client, channel_id)
            for channel_id in CHANNEL_IDS
        ]

        # Run all channels in parallel, isolated
        await asyncio.gather(*tasks, return_exceptions=True)
