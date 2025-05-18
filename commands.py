from fastapi import FastAPI, Request
# import aiohttp
from lxml import html
import httpx
from utils import (
    SlashCommand,
    Option,
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
        response = await client.get(f"https://ev.io/stats-by-un/{username}", timeout=30)
        if response.status_code != 200:
            return None
        data = response.json()
        return data[0] if data else None

#already deferred in main.py to reduce latency   
# async def defer_response( interaction_id, interaction_token):
#     """Send a deferred response to Discord."""
#     url = f"https://discord.com/api/v10/interactions/{interaction_id}/{interaction_token}/callback"
#     payload = {"type": 5}  # 5 = DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
#     headers = {"Content-Type": "application/json"}
#     requests.post(url, json=payload, headers=headers)

async def send_followup(interaction_token,payload):
    """Send the follow-up response after processing."""
    url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}"
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
        # interaction_id = json_data["id"]

        # await defer_response(interaction_id, interaction_token)
        username = json_data["data"]["options"][0]["value"]
        data = await getUserData(username)
        
        if not data:
            
            payload = {"content": "Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return
        
        # skin_data = requests.get(f'https://ev.io/node/{data["field_eq_skin"][0]["target_id"]}?_format=json').json()
        async with httpx.AsyncClient() as client:
            skin_data = await client.get(f'https://ev.io/node/{data["field_eq_skin"][0]["target_id"]}?_format=json', timeout=30)
            skin_data = skin_data.json()
        
        UserID=data['uid'][0]['value']
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ev.io/user/{UserID}", timeout=30)
        xpa='//*[(@id = "block-views-block-clans-block-4")]//*[contains(concat( " ", @class, " " ), concat( " ", "img-responsive", " " ))]'
        res=html.fromstring(response.content).xpath(xpa)
        if res:
            url=res[0].attrib['src']
            ClanThumbnail="https://www.ev.io"+url
        else:
            ClanThumbnail=skin_data["field_profile_thumb"][0]["url"]


        
        
        # Parse account creation date
        datetime_string = data["created"][0]["value"]
        parsed_datetime = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S%z')
        current_datetime = datetime.now(parsed_datetime.tzinfo)
        days_past = (current_datetime - parsed_datetime).days
        formatted_date = parsed_datetime.strftime('%d/%m/%Y')
        
        # First embed: Player Image
        image_embed = {
            "description":f'[**{data["name"][0]["value"]}**](https://ev.io/user/{data["uid"][0]["value"]})',
            "color": 16776960,  # Yellow
            # "title":f'[{data["name"][0]["value"]}](https://ev.io/user/{data["uid"][0]["value"]})',
            # "fields": [
            #     {"name": "Username", "value": f'[{data["name"][0]["value"]}](https://ev.io/user/{data["uid"][0]["value"]})', "inline": False}
            # ],
            "thumbnail": {"url": ClanThumbnail},
            "image": {"url": skin_data["field_large_thumb"][0]["url"]},
        }
        
        # Second embed: Player Stats
        stats_embed = {
            "color": 16776960,  # Yellow
            "fields": [
                {"name": "Kills", "value": str(data["field_kills"][0]["value"]), "inline": False},
                {"name": "Deaths", "value": str(data["field_deaths"][0]["value"]), "inline": False},
                {"name": "K/D", "value": str(data["field_k_d"][0]["value"]), "inline": False},
                {
                    "name": "Kills Per Game",
                    "value": str(round(data["field_kills"][0]["value"] / data["field_total_games"][0]["value"], 2)) 
                            if data["field_total_games"][0]["value"] != 0 else "N/A",
                    "inline": False
                },
                {"name":"CP this week", "value":f'{data["field_cp_earned_weekly"][0]["value"]}'},
                {"name":"CP all time", "value":f'{data["field_lifetime_cp_earned"][0]["value"]}'}

                ,{"name": "Date of account creation", "value": formatted_date, "inline": False},
                {"name": "Days past", "value": str(days_past), "inline": False},
            ]
        }
        payload = {"embeds": [image_embed, stats_embed]}            
        await send_followup(interaction_token=interaction_token,payload=payload)
        # return {
        #     "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        #     "data": {"embeds": [image_embed, stats_embed]},
        # }

class GetClanRanking(SlashCommand):
    def __init__(self):
        super().__init__(
            name="cpranking",
            description="Display the CP rankings of a clan by group name or group number, defaults to Assassins clan.",
            options=[
                Option(
                    name="groupnumber",
                    type=ApplicationCommandOptionType.STRING,
                    description="Clan number to fetch CP Ranking",
                    required=False,
                ),
                Option(
                    name="clan",
                    type=ApplicationCommandOptionType.STRING,
                    description="Name of the clan to fetch CP Ranking",
                    required=False,
                )
            ],
        )



    async def respond(self, json_data: dict):
    

        interaction_token = json_data["token"]
        # interaction_id = json_data["id"]

        # await defer_response(interaction_id, interaction_token)

        options = json_data.get("data", {}).get("options", [])
        group_number = "903"  # Default group number
        clan_name = None

        if options:
            option = options[0]
            if option["name"] == "groupnumber":
                group_number = option["value"]
            elif option["name"] == "clan":
                clan_name = option["value"]
                async with httpx.AsyncClient() as client:
                    clans = await client.get("https://ev.io/clans-all3", timeout=30)
                    clans=clans.json()
                    found=False
                    for clan in clans:
                        if clan["clan_name"]==clan_name:
                            group_number=clan["cid"]
                            found=True
                            break
                    if not found:
                        payload = {"content": "Clan not found\n*Roar?*"}
                        await send_followup(interaction_token=interaction_token,payload=payload)
                        return


        # response = requests.get(f"https://ev.io/group/{group_number}")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ev.io/group/{group_number}", timeout=30)
        tree =  html.fromstring(response.content)
        matches = tree.xpath("//td")
        
        if not matches:
            payload = {"content": "Clan not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return
        scores = []

        for i in range(0, len(matches), 4):
            scores.append({
                "name": matches[i].text_content().strip() + "." + matches[i + 1].text_content().strip(),
                "value": matches[i + 2].text_content().strip(),
                "inline": True,
            })

        stats_embed = {
            "thumbnail":{"url":"https://ev.io"+tree.xpath('//*[(@id = "block-views-block-clans-block-2")]//*[contains(concat( " ", @class, " " ), concat( " ", "field-content", " " ))]//*[contains(concat( " ", @class, " " ), concat( " ", "img-responsive", " " ))]')[0].attrib['src']},
            "color": 16776960,  # Yellow
            "fields": scores[:15], 
            "description":f"""[**{tree.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "page-header", " " ))]')[0].text}**](https://ev.io/group/{group_number})""" 
        }
        payload = {"embeds": [stats_embed]}
        await send_followup(interaction_token,payload=payload)        

class GetClanRank(SlashCommand):
    def __init__(self):
        super().__init__(
            name="clanrank",
            description="Display the weekly clans ranking.",
        )



    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ev.io/clans", timeout=30)
        tree = html.fromstring(response.content)
        matches = tree.xpath('//td[contains(concat( " ", @class, " " ), concat( " ", "is-active", " " ))] | //*[contains(concat( " ", @class, " " ), concat( " ", "img-responsive", " " ))] | //td//a | //td[contains(concat( " ", @class, " " ), concat( " ", "views-field-counter", " " ))]')

        scores = []


        for i in range(0, len(matches),4):
            clan={}
            clan["name"]=matches[i].text_content().strip()+"."+matches[i+2].text_content().strip()
            clan["value"]=matches[i+3].text_content().strip()
            clan["image"]="ev.io"+matches[i+1].attrib['src']
            clan["inline"]=False
            scores.append(clan)

        stats_embed = {
            "color": 16776960,  # Yellow
            "fields": scores[:10],  
        }
        payload={"embeds": [stats_embed]}
        await send_followup(interaction_token,payload=payload)        

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
        # interaction_id = json_data["id"]
        # await defer_response(interaction_id, interaction_token)
        username = json_data["data"]["options"][0]["value"]
        data = await getUserData(username)


        if not data:
            payload = {"content": "Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return

        data['field_survival_high_scores'][0]['value'].pop('caption', None)
        data['field_survival_high_scores'][0]['value'].pop('0', None)

        # Create an embed
        sstat = discord.Embed(color=discord.Color.yellow())

        for value in data['field_survival_high_scores'][0]['value'].values():
            sstat.add_field(name=value[0], value=value[1], inline=True)

        payload = {
            "embeds": [sstat.to_dict()]
        }
        await send_followup(interaction_token=interaction_token,payload=payload) 
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
        # interaction_id = json_data["id"]
        # await defer_response(interaction_id, interaction_token)

        username = json_data["data"]["options"][0]["value"]
        data =  await getUserData(username)
        
        if not data:
            payload = {"content": "Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        if not data["field_custom_crosshair"]:
            payload = {"content": "Player has no custom crosshair\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        embeds = [
            {
                "color": 16776960,  # Yellow
                "image": {"url": data["field_custom_crosshair"][0]["url"]},
            }
        ]
        payload = {
            "embeds": embeds
        }
        await send_followup(payload=payload,interaction_token=interaction_token)        
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
        payload = {
            "embeds": embeds
        }
        await send_followup(interaction_token,payload=payload)
async def fetch_csrf_tokens(client):
    """Fetches CSRF tokens required for form submission."""
    try:
        response = await client.get("https://ev.io/group/903/edit")
        response.raise_for_status()
        
        tree = html.fromstring(response.text)
        form_build_id = tree.xpath("//input[@name='form_build_id']/@value")[0]
        form_token = tree.xpath("//input[@name='form_token']/@value")[0]

        return form_build_id, form_token
    except Exception as e:
        print(f"Error fetching CSRF tokens: {e}")
        return None, None
async def deploy_new(field_deployed_values):
    from dotenv import load_dotenv
    load_dotenv()
    COOKIES={os.environ.get("KEY") : os.environ.get("VALUE") }
    """Submits form data asynchronously."""
    async with httpx.AsyncClient(cookies=COOKIES) as client:
        form_build_id, form_token = await fetch_csrf_tokens(client)
        if not form_build_id or not form_token:
            print("Failed to retrieve CSRF tokens. Aborting.")
            return

        # Form Data
        form_data = {
            "label[0][value]": "The Assassins",
            "form_build_id": form_build_id,
            "form_token": form_token,
            "form_id": "group_clan_edit_form",
            "field_insignia[0][fids]": "10364",
            "field_insignia[0][display]": "1",
            "field_banner[0][fids]": "94990",
            "field_banner[0][display]": "1",
            "field_motto[0][value]": "Fear not the darkness, But welcome its Embrace",
            "field_discord_link[0][uri]": "https://discord.gg/sSGzVXP6Fy",
            "op": "Save"
        }

        # Add deployed values dynamically
        for value in field_deployed_values:
            form_data[f"field_deployed[{value}]"] = str(value)

        # Convert to multipart
        files = {key: (None, value) for key, value in form_data.items()}

        try:
            response = await client.post("https://ev.io/group/903/edit", files=files)
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Error submitting form: {e}")
class Deploy(SlashCommand):

    def __init__(self):
        super().__init__(
            name="deploy",
            description="Deploy yourself!",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to deploy",
                    required=True,
                )
            ],
        )

    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        # interaction_id = json_data["id"]
        # await defer_response(interaction_id, interaction_token)

        username = json_data["data"]["options"][0]["value"]
        data =  await getUserData(username)
        
        if not data:
            payload = {"content": "Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        import hashlib
        hash=hashlib.sha256(f'{json_data["member"]["user"]["id"]}Samael{username}'.encode()).hexdigest()
        if  not (data['field_social_bio']) or  (hash) not in data['field_social_bio'][0]['value'] :
            payload = {"content": f"Please modify your ev.io social_bio to include {hash}\nhttps://ev.io/user/<your_user_ID>/edit"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        
        cd=requests.get("https://ev.io/group/903?_format=json").json()
        deployed=[]
        for element in cd['field_deployed']:
            deployed.append(element['target_id'])
        deployed.pop()
        deployed.insert(0,data["uid"][0]["value"])

        # Run asynchronously
        await   deploy_new(deployed)
        

        payload = {"content": f"Deployed {username}!" }
        await send_followup(interaction_token=interaction_token, payload=payload)
class ClanPlayersStatus(SlashCommand):

    def __init__(self):
        super().__init__(
            name="clanplayersstatus",
            description="Get a list of online players in The Assasins along with a link to join their game.",
            options=[
          
            ],
        )


    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        async def GetClanData():
            import websocket
            import json

            clan_data_container = {"data": None}  # Use a mutable container

            def on_open(ws):
                print("WebSocket connection opened.")
                message = {
                    "header": "identify",
                    "uid": int(os.environ.get("UID")),
                    "id": os.environ.get("ID"),
                }
                ws.send(json.dumps(message))

            def on_message(ws, message):
                data = json.loads(message)
                if data.get("header") == "clanPlayersAndStatus":
                    clan_data_container["data"] = data
                    ws.close()

            def on_close(ws, close_status_code, close_msg):
                print("WebSocket closed:", close_status_code, close_msg)
                pass

            def on_error(ws, error):
                pass

            headers = {
                "Upgrade": "websocket",
                "Sec-GPC": "1",
                "Origin": "https://ev.io",
                "Cache-Control": "no-cache",
                "Accept-Language": "en-US,en;q=0.9",
                "Pragma": "no-cache",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "KALkq8N0UycMo5tC2MWeZA==",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Sec-WebSocket-Version": "13",
                "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
            }

            websocket.enableTrace(True)
            ws = websocket.WebSocketApp(
                "wss://social.ev.io/",
                header=[f"{k}: {v}" for k, v in headers.items()],
                on_open=on_open,
                on_message=on_message,
                on_close=on_close,
                on_error=on_error
            )

            ws.run_forever()
            return clan_data_container["data"]
        
        UID_= int(os.environ.get("UID"))
        message=""
        OnlinePlayers= await GetClanData()
        for player in OnlinePlayers['players']:
            if not player['status'].startswith("offline") and player['uid'] != UID_:
                message=message+ f"[{player['username']}]({player['gameJoinURL']})\n"

        if not message:
            payload = {"content": "No clan mates online!\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        payload = {
            "content": f"Online players:\n{message}"
        }
        await send_followup(interaction_token=interaction_token,payload=payload)  


commands = [CheckPlayerStats(),CheckSurvivalScores(),GetCrosshair(),PeekSkins(),GetClanRanking(),GetClanRank(), Deploy(),ClanPlayersStatus()]


@app.post("/")
async def handle_interaction(request: Request):
    data = await request.json()
    command_name = data.get("data", {}).get("name")
    
    for command in commands:
        if command.name == command_name:
            return await command.respond(data)
    
    return {"error": "Unknown command"}
