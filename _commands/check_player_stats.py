from . import send_followup

import httpx
from lxml import html
import httpx
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)

from datetime import datetime

from ev import getUserData
from urllib.parse import quote
class CheckPlayerStats(SlashCommand):
    def __init__(self):
        super().__init__(
            name="checkplayerstats",
            description="Display the stats of a player from a Username.",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to fetch stats for",
                    required=True,
                )
            ],
        )
    
    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        username = json_data["data"]["options"][0]["value"]
        data = await getUserData(username)  

        if not data:
            payload = {"content": "⚠️ Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return

        async with httpx.AsyncClient() as client:
            skin_response = await client.get(f'https://ev.io/node/{data["field_eq_skin"][0]["target_id"]}?_format=json', timeout=30)
            skin_data = skin_response.json()

        user_id = data['uid'][0]['value']
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ev.io/user/{user_id}", timeout=30)

        xpa = '//*[(@id = "block-views-block-clans-block-4")]//*[contains(concat(" ", @class, " "), " img-responsive ")]'
        res = html.fromstring(response.content).xpath(xpa)

        clan_thumbnail = f'https://www.ev.io{res[0].attrib["src"]}' if res else skin_data["field_profile_thumb"][0]["url"]

        # Parse creation and last seen dates
        created_dt = datetime.strptime(data["created"][0]["value"], '%Y-%m-%dT%H:%M:%S%z')
        last_seen_dt = datetime.strptime(data["changed"][0]["value"], '%Y-%m-%dT%H:%M:%S%z')

        days_past = (datetime.now(created_dt.tzinfo) - created_dt).days
        formatted_created = created_dt.strftime('%d %b %Y')
        formatted_last_seen = last_seen_dt.strftime('%d %b %Y %H:%M UTC')

        # First Embed: Player and Skin
        image_embed = {
            "title": f'**{data["name"][0]["value"]}**',
            "url": f'https://ev.io/user/{user_id}',
            "color": 0xF1C40F,
            "thumbnail": {"url": clan_thumbnail},
            "image": {"url": skin_data["field_large_thumb"][0]["url"]},
            "description": f'[🔍 View Skin](https://luc4-evskinviewer.vercel.app/?nid={data["field_eq_skin"][0]["target_id"]})\n[📈 More Stats](https://ev-lobby.vercel.app/?username={quote(username)})'
        }

        def get_value(data, key, default=0):
            """Safely get value from a field list like [{'value': X}] or return default."""
            field = data.get(key, [])
            return field[0]["value"] if field else default

        kills = get_value(data, "field_kills", 0)
        deaths = get_value(data, "field_deaths", 0)
        kd_ratio = get_value(data, "field_k_d", "0.00")
        total_games = get_value(data, "field_total_games", 0)
        kpg = round(kills / total_games, 2) if total_games else "N/A"

        e_balance = get_value(data, "field_ev_coins", 0)
        weekly_e = get_value(data, "field_ev_coins_this_week", 0)
        rank = get_value(data, "field_rank", "N/A")


        
        

        # Second Embed: Stats
        stats_embed = {
            "title": "📊 Stats Overview",
            "color": 0xF1C40F,
        "fields": [
            {"name": "🔫 Kills", "value": f"**{kills}**", "inline": True},
            {"name": "💀 Deaths", "value": f"**{deaths}**", "inline": True},
            {"name": "📈 K/D Ratio", "value": f"**{kd_ratio}**", "inline": True},

            {"name": "🎮 Games Played", "value": f"**{total_games}**", "inline": True},
            {"name": "🔥 Kills/Game", "value": f"**{kpg}**", "inline": True},

            {"name": "🛡️ CP (Weekly)", "value": f"**{data['field_cp_earned_weekly'][0]['value']}**", "inline": True},
            {"name": "🪙 e balance", "value": f"**{e_balance} e**", "inline": True},
            {"name": "🪙 e earned this week", "value": f"**{weekly_e} e**", "inline": True},

            {"name": "🏅 Rank", "value": f"**#{rank}**", "inline": True},
            {"name": "📅 Account Created", "value": f"**{formatted_created}**", "inline": True},
            {"name": "⏳ Days Since", "value": f"**{days_past}**", "inline": True},
            {"name": "🟢 Last Seen", "value": f"**{formatted_last_seen}**", "inline": False},
            ]

        }

        payload = {"embeds": [image_embed, stats_embed]}
        await send_followup(interaction_token=interaction_token, payload=payload)
