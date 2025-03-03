from fastapi import FastAPI, Request
# import aiohttp
from lxml import html
import httpx
from utils import (
    SlashCommand,
    Option,
    InteractionResponseType,
    ApplicationCommandOptionType,
    # InteractionResponseFlags
)
import os
import requests
from datetime import datetime
import discord

app = FastAPI()
# class ByeCommand(SlashCommand):
#     def __init__(self):
#         super().__init__(
#             name="bye",
#             description="Say bye to someone",
#             options=[
#                 Option(
#                     name="user",
#                     type=ApplicationCommandOptionType.USER,
#                     description="The user to say bye",
#                     required=True,
#                 ),
#             ],
#         )

#     async def respond(self, json_data: dict):
#         # This function is async just so that fastapi supports async poggies
#         user_id = json_data["data"]["options"][0]["value"]
#         return {
#             "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
#             "data": {
#                 "content": f"Bye <@!{user_id}>",
#                 "flags": InteractionResponseFlags.EPHEMERAL,
#             },
#         }
# class HelloCommand(SlashCommand):
#     def __init__(self):
#         super().__init__(
#             name="hello",
#             description="Say hello to someone",
#             options=[
#                 Option(
#                     name="user",
#                     type=ApplicationCommandOptionType.USER,
#                     description="The user to say hello",
#                     required=True,
#                 ),
#             ],
#         )

#     async def respond(self, json_data: dict):
#         # This function is async just so that fastapi supports async poggies
#         user_id = json_data["data"]["options"][0]["value"]
#         return {
#             "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
#             "data": {
#                 "content": f"Hello <@!{user_id}>",
#                 "flags": InteractionResponseFlags.EPHEMERAL,
#             },
#         }

async def getUserData(username):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://ev.io/stats-by-un/{username}")
        if response.status_code != 200:
            return None
        data = response.json()
        return data[0] if data else None
    
async def defer_response( interaction_id, interaction_token):
    """Send a deferred response to Discord."""
    url = f"https://discord.com/api/v10/interactions/{interaction_id}/{interaction_token}/callback"
    payload = {"type": 5}  # 5 = DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

async def send_followup(interaction_token, message, embeds):
    """Send the follow-up response after processing."""
    url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}"
    payload = {"content": message, "embeds": embeds}
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

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
        interaction_id = json_data["id"]

        await defer_response(interaction_id, interaction_token)
        username = json_data["data"]["options"][0]["value"]
        data = await getUserData(username)
        
        if not data:
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": "Player not found\n*Roars*"},
            }
        
        # skin_data = requests.get(f'https://ev.io/node/{data["field_eq_skin"][0]["target_id"]}?_format=json').json()
        async with httpx.AsyncClient() as client:
            skin_data = await client.get(f'https://ev.io/node/{data["field_eq_skin"][0]["target_id"]}?_format=json')
            skin_data = skin_data.json()
        
        # Parse account creation date
        datetime_string = data["created"][0]["value"]
        parsed_datetime = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S%z')
        current_datetime = datetime.now(parsed_datetime.tzinfo)
        days_past = (current_datetime - parsed_datetime).days
        formatted_date = parsed_datetime.strftime('%d/%m/%Y')
        
        # First embed: Player Image
        image_embed = {
            "color": 16776960,  # Yellow
            "fields": [
                {"name": "Username", "value": data["name"][0]["value"], "inline": False}
            ],
            "thumbnail": {"url": skin_data["field_profile_thumb"][0]["url"]},
            "image": {"url": skin_data["field_large_thumb"][0]["url"]},
        }
        
        # Second embed: Player Stats
        stats_embed = {
            "color": 16776960,  # Yellow
            "fields": [
                {"name": "Kills", "value": str(data["field_kills"][0]["value"]), "inline": False},
                {"name": "Deaths", "value": str(data["field_deaths"][0]["value"]), "inline": False},
                {"name": "K/D", "value": str(data["field_k_d"][0]["value"]), "inline": False},
                {"name": "Kills Per Game", "value": str(round(data["field_kills"][0]["value"] / data["field_total_games"][0]["value"], 2)), "inline": False},
                {"name": "Date of account creation", "value": formatted_date, "inline": False},
                {"name": "Days past", "value": str(days_past), "inline": False},
            ]
        }
        
        await send_followup(interaction_token=interaction_token, message="*Roars!*",embeds=[image_embed,stats_embed])
        # return {
        #     "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        #     "data": {"embeds": [image_embed, stats_embed]},
        # }

class GetClanRanking(SlashCommand):
    def __init__(self):
        super().__init__(
            name="cpranking",
            description="Display the CP rankings of a clan by group ID, defaults to Assassins clan.",
            options=[
                Option(
                    name="groupnumber",
                    type=ApplicationCommandOptionType.STRING,
                    description="Clan number to fetch CP Ranking",
                    required=False,
                )
            ],
        )



    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        interaction_id = json_data["id"]

        await defer_response(interaction_id, interaction_token)

        options = json_data.get("data", {}).get("options", [])
        group_number = options[0]["value"] if options else "903"  # Default to 903 if not provided

        # response = requests.get(f"https://ev.io/group/{group_number}")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ev.io/group/{group_number}")
        tree = html.fromstring(response.content)
        matches = tree.xpath("//td")

        scores = []
        if not matches:
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": "Player not found\n*Roars*"},
            }

        for i in range(0, len(matches), 4):
            scores.append({
                "name": matches[i].text_content().strip() + "." + matches[i + 1].text_content().strip(),
                "value": matches[i + 2].text_content().strip(),
                "inline": True,
            })

        stats_embed = {
            "color": 16776960,  # Yellow
            "fields": scores[:15],  
        }

        await send_followup(interaction_token, "*Roars*", [stats_embed])        

class CheckSurvivalScores(SlashCommand):
    def __init__(self):
        super().__init__(
            name="survivalscores",
            description="Get Survival highscores of a player by map.",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to fetch survival scores for",
                    required=True,
                )
            ],
        )
    
    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        interaction_id = json_data["id"]
        await defer_response(interaction_id, interaction_token)
        username = json_data["data"]["options"][0]["value"]
        data = await getUserData(username)


        if not data:
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": "Player not found\n*Roars*"},
            }

        data['field_survival_high_scores'][0]['value'].pop('caption', None)
        data['field_survival_high_scores'][0]['value'].pop('0', None)

        # Create an embed
        sstat = discord.Embed(color=discord.Color.yellow())

        for value in data['field_survival_high_scores'][0]['value'].values():
            sstat.add_field(name=value[0], value=value[1], inline=True)


        await send_followup(interaction_token=interaction_token,embeds=[sstat.to_dict()], message="" )
        # return {
        #     "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        #     "data": {
        #         "embeds": [sstat.to_dict()]  
        #     },
        # }


class GetCrosshair(SlashCommand):
    def __init__(self):
        super().__init__(
            name="getcrosshair",
            description="Get the crosshair of a user from username.",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to fetch crosshair for",
                    required=True,
                )
            ],
        )

    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        interaction_id = json_data["id"]
        await defer_response(interaction_id, interaction_token)

        username = json_data["data"]["options"][0]["value"]
        data =  await getUserData(username)
        
        if not data:
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": "Player not found\n*Roars*"},
            }
        
        embeds = [
            {
                "color": 16776960,  # Yellow
                "image": {"url": data["field_custom_crosshair"][0]["url"]},
            }
        ]
        await send_followup(message="",interaction_token=interaction_token, embeds=embeds)        
        # return {
        #     "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        #     "data": {"content": "*Roars*", "embeds": embeds},
        # }
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

        # Acknowledge the interaction (defer reply)
        interaction_token = json_data["token"]
        interaction_id = json_data["id"]
        await self.defer_response(interaction_id, interaction_token)

        # Process the request (fetch user data)
        data = await getUserData(username)

        # Create embed objects
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
                    response = await client.get(f'https://ev.io{data[field][0]["url"]}?_format=json')
                    skin_data = response.json()
                # skin_data = requests.get(f'https://ev.io{data[field][0]["url"]}?_format=json').json()
                embed = {
                    "color": 16776960,
                    "image": {"url": skin_data["field_weapon_skin_thumb"][0]["url"]},
                    "description": f'[{name}](https://ev.io{data[field][0]["url"]})'
                }
                embeds.append(embed)
            except Exception as e:
                print(f"Error fetching {name}: {e}")

        # Send the follow-up message
        await self.send_followup(interaction_token, "*Roars*", embeds)

    async def defer_response(self, interaction_id, interaction_token):
        """ Send a defer response to Discord """
        url = f"https://discord.com/api/v10/interactions/{interaction_id}/{interaction_token}/callback"
        payload = {"type": 5}  # 5 = DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=payload, headers=headers)

    async def send_followup(self, interaction_token, message, embeds):
        """ Send the follow-up response after processing """
        url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}"
        payload = {"content": message, "embeds": embeds}
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=payload, headers=headers)    
commands = [CheckPlayerStats(),CheckSurvivalScores(),GetCrosshair(),PeekSkins(),GetClanRanking()]


@app.post("/")
async def handle_interaction(request: Request):
    data = await request.json()
    command_name = data.get("data", {}).get("name")
    
    for command in commands:
        if command.name == command_name:
            return await command.respond(data)
    
    return {"error": "Unknown command"}
