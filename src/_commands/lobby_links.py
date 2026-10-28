from . import send_followup

import asyncio

import httpx

import cloudscraper

import json

import re

import random

from ..utils import SlashCommand


BUNDLE_URL = "https://ev.io/dist/1-7-0/public/bundle.js"


def getCount(url: str) -> str:
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(
            f"{url}players{random.random()}",
            timeout=5
        )
        return str(json.loads(r.text)["playerCount"])
    except Exception:
        return "N/A"


async def fetch_lobby_links():
    """
    Fetch active lobbies and their player counts.

    Returns:
        List of dictionaries containing:
        region, url, player_count, id, gamemode
    """

    # ---------------------------
    # Fetch lobby list
    # ---------------------------

    async with httpx.AsyncClient() as client:
        r = await client.get(BUNDLE_URL)

    match = re.search(
        r'(\[\s*\{"id":"lobby-.*?\}\s*\])',
        r.text,
        re.DOTALL
    )

    if not match:
        return []

    data = json.loads(match.group(1))

    # ---------------------------
    # Prepare URLs
    # ---------------------------

    urls = [
        game["connectionUrl"].replace("wss", "https")
        for game in data
    ]

    # ---------------------------
    # Fetch player counts
    # ---------------------------

    semaphore = asyncio.Semaphore(16)

    async def fetch_count(url):
        async with semaphore:
            return await asyncio.to_thread(
                getCount,
                url
            )

    counts = await asyncio.gather(
        *(fetch_count(url) for url in urls)
    )

    # ---------------------------
    # Return useful information
    # ---------------------------

    return [
        {
            "region": game["region"],
            "url": url,
            "player_count": count,
            "id": game["id"],
            "gamemode": game["gamemode"],
        }
        for game, url, count in zip(data, urls, counts)
    ]


class LobbyLinks(SlashCommand):

    def __init__(self):
        super().__init__(
            name="gamelinks",
            description="Get a list of links for all active lobbies.",
            options=[],
        )

    async def respond(self, json_data: dict):

        interaction_token = json_data["token"]

        # ---------------------------
        # Fetch lobby information
        # ---------------------------

        lobbies = await fetch_lobby_links()

        if not lobbies:
            await send_followup(
                interaction_token=interaction_token,
                payload={
                    "content": "Lobby data is temporarily unavailable."
                },
            )
            return

        # ---------------------------
        # Formatting
        # ---------------------------

        msg1 = ""
        msg2 = ""

        seen = []
        k = 0

        for lobby in lobbies:

            gm = lobby["gamemode"]

            if gm not in seen:
                seen.append(gm)
                k += 1

                if k > 5:
                    msg2 += f"\n{gm}"
                else:
                    msg1 += f"\n{gm}"

            line = (
                f"\n\t\t{lobby['region']} "
                f"[ev.io 🔗](<https://ev.io/?game={lobby['id']}>) "
                f"[players: {lobby['player_count']}]"
            )

            if k > 5:
                msg2 += line
            else:
                msg1 += line

        # ---------------------------
        # Send
        # ---------------------------

        if msg1:
            await send_followup(
                interaction_token=interaction_token,
                payload={"content": msg1}
            )

        if msg2:
            await send_followup(
                interaction_token=interaction_token,
                payload={"content": msg2}
            )