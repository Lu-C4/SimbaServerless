from . import send_followup
import httpx
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)
from ev import getUserData

class PeekSkins(SlashCommand):
    def __init__(self):
        super().__init__(
            name="peekskins",
            description="Get the skins of a user from username.",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to fetch skins for",
                    required=True,
                )
            ],
        )

    async def respond(self, json_data: dict):
        username = json_data["data"]["options"][0]["value"]
        interaction_token = json_data["token"]


        data = await getUserData(username)
        if not data:
            payload = {"content": "Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return

        skins = [
            ("field_auto_rifle_skin", "Assault Rifle"),
            ("field_laser_rifle_skin", "Laser Rifle"),
            ("field_sweeper_skin", "Sweeper"),
            ("field_burst_rifle_skin", "Burst Rifle"),
            ("field_hand_cannon_skin", "Hand Cannon"),
            ("field_sword_skin", "Sword"),
        ]

        embeds = []
        for field, name in skins:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f'https://ev.io{data[field][0]["url"]}?_format=json', timeout=30)
                    skin_data = response.json()
                embed = {
                    "color": 16776960,
                    "image": {"url": skin_data["field_weapon_skin_thumb"][0]["url"]},
                    "description": f'[View skin 🔍](https://luc4-evskinviewer.vercel.app/?nid={data[field][0]["target_id"]})',
                    "title":name,
                    "url":f'https://ev.io{data[field][0]["url"]}'
                }
                embeds.append(embed)
            except Exception as e:
                print(f"Error fetching {name}: {e}")

        payload = {
            "embeds": embeds
        }
        await send_followup(interaction_token,payload=payload)
