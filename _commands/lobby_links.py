from . import send_followup
import httpx
import cloudscraper
import json
import re
import random
import os

from utils import SlashCommand
from concurrent.futures import ThreadPoolExecutor, as_completed


BUNDLE_URL = "https://ev.io/dist/1-7-0/public/bundle.js"


def getCount(url: str) -> str:
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(f"{url}players{random.random()}", timeout=5)
        return str(json.loads(r.text)["playerCount"])
    except Exception:
        return "N/A"


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
        # Fetch lobby list (async once)
        # ---------------------------
        async with httpx.AsyncClient() as client:
            r = await client.get(BUNDLE_URL)

        match = re.search(
            r'(\[\s*\{"id":"lobby-.*?\}\s*])',
            r.text,
            re.DOTALL
        )
        data = json.loads(match.group(1))

        # ---------------------------
        # Prepare URLs (NO extra work)
        # ---------------------------
        urls = [
            game["connectionUrl"].replace("wss", "https")
            for game in data
        ]

        # ---------------------------
        # THREADPOOL — FULL BLAST
        # ---------------------------
        max_workers = min(64, (os.cpu_count() or 1) * 8)

        counts = [None] * len(urls)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(getCount, urls[i]): i
                for i in range(len(urls))
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    counts[idx] = future.result()
                except Exception:
                    counts[idx] = "N/A"
            
        # ---------------------------
        # Formatting AFTER network
        # ---------------------------
        msg1 = ""
        msg2 = ""
        seen = []
        k = 0

        for game, count in zip(data, counts):
            gm = game["gamemode"]

            if gm not in seen:
                seen.append(gm)
                k += 1
                if k > 5:
                    msg2 += f"\n{gm}"
                else:
                    msg1 += f"\n{gm}"

            line = (
                f"\n\t\t{game['region']} "
                f"<https://ev.io/?game={game['id']}> "
                f"[players: {count}]"
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
