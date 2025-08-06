from fastapi import FastAPI
from lxml import html
import httpx
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)
import os
from datetime import datetime
import discord

from ev import getUserData,deploy_new,getDeployedList,getUserNameByID

app = FastAPI()






async def send_followup(interaction_token,payload):
    """Send the follow-up response after processing."""
    url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}"
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code!=200:
        print(response.text)


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
            "title": f'🏹 **{data["name"][0]["value"]}**',
            "url": f'https://ev.io/user/{user_id}',
            "color": 0xF1C40F,
            "thumbnail": {"url": clan_thumbnail},
            "image": {"url": skin_data["field_large_thumb"][0]["url"]},
            "description": f'[🔍 View Skin](https://luc4-evskinviewer.vercel.app/?nid={data["field_eq_skin"][0]["target_id"]})'
        }

        # Gather player stats
        kills = data["field_kills"][0]["value"]
        deaths = data["field_deaths"][0]["value"]
        kd_ratio = data["field_k_d"][0]["value"]
        total_games = data.get("field_total_games", [{"value": 0}])[0]["value"]
        kpg = round(kills / total_games, 2) if total_games else "N/A"

        e_balance = data["field_ev_coins"][0]["value"]
        weekly_e = data["field_ev_coins_this_week"][0]["value"]
        rank = data.get("field_rank", [{"value": "N/A"}])[0]["value"]

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
        payload = {
            "embeds": [
                {
                    "color": 16776960,
                    "image": {
                        "url": data["field_custom_crosshair"][0]["url"]
                    },
                }
            ],
            "components": [
                {
                    "type": 1,  # Action row
                    "components": [
                        {
                            "type": 2,  # Button
                            "style": 5,  # Link style
                            "label": "Download",
                            "url": data["field_custom_crosshair"][0]["url"]
                        }
                    ]
                }
            ]
        }

        await send_followup(payload=payload,interaction_token=interaction_token)        

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
                    "description": f'[{name}](https://ev.io{data[field][0]["url"]})'
                }
                embeds.append(embed)
            except Exception as e:
                print(f"Error fetching {name}: {e}")

        payload = {
            "embeds": embeds
        }
        await send_followup(interaction_token,payload=payload)
        
class Deploy(SlashCommand):

    def __init__(self):
        super().__init__(
            name="self_deploy",
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
        from ev import getClanData
        cd= await getClanData()
        deployed=[]
        for element in cd['field_deployed']:
            deployed.append(element['target_id'])
        
        if len(deployed)==20:
            undeployed=deployed.pop()
            payload = {"content": f"Deployed **{username}** instead of  **{ await getUserNameByID(undeployed)}**!" }
        else:
            payload={"content": f"Deployed {username}!"}
        
        deployed.insert(0,data["uid"][0]["value"])
        
        status = await deploy_new(deployed)
        
        if not status:
            payload={"content":"Whoops! That did not work!\nTry again or contact a Commander , Lieutenant or a Moderator and ask them to use /deploy"}
            
        
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
        import websockets
        import json
        async def GetClanData():
            """Connect to WebSocket and retrieve clan player data."""
            uri = "wss://social.ev.io/"
            headers = {
                "Origin": "https://ev.io",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            }

            async with websockets.connect(uri, additional_headers=headers) as websocket_conn:

                identify_msg = {
                    "header": "identify",
                    "uid": int(os.environ.get("UID")),
                    "id": os.environ.get("ID"),
                }
                await websocket_conn.send(json.dumps(identify_msg))


                while True:
                    msg = await websocket_conn.recv()
                    data = json.loads(msg)

                    if data.get("header") == "clanPlayersAndStatus":
                        return data
        
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

class LobbyLinks(SlashCommand):

    def __init__(self):
        super().__init__(
            name="gamelinks",
            description="Get a list of links for all active lobbies.",
            options=[
          
            ],
        )


    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]

        message=""
        message2=""


        import re
        import json

        url = "https://ev.io/dist/1-7-0/public/bundle.js"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        raw_text = response.text
        match = re.search(r'(\[\s*\{"id":"lobby-.*?\}\s*])', raw_text, re.DOTALL)
        json_str = match.group(1)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            exit()

        gamemode = []
        k=0
        for game in data:
            if game['gamemode'] not in gamemode:
                k+=1
                gamemode.append(game['gamemode'])
                if k>5:
                    message2+= '\n' + (game['gamemode'])
                    
                else:
                    message+= '\n' + (game['gamemode'])

            if k>5:
                message2+=f"\n\t\t{game['region']} <https://ev.io/?game={game['id']}>"
            else:
                message+=f"\n\t\t{game['region']} <https://ev.io/?game={game['id']}>"


        payload = {
            "content": message
        }
        payload2 = {
            "content": message2
        }
        
        await send_followup(interaction_token=interaction_token,payload=payload) 
        await send_followup(interaction_token=interaction_token,payload=payload2)

class SuperDeploy(SlashCommand):
    def __init__(self):
        super().__init__(
            name="deploy",
            description="Deploy a player.",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to deploy",
                    required=True,
                )
            ]
        )

    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        
        username = json_data["data"]["options"][0]["value"]
        UserData=await getUserData(username=username)
        if not UserData:
            payload={"content":"Player not found!"}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return
        
        roles=set(json_data['member']['roles'])

        if roles.intersection(set(os.environ.get('ALLOWED_ROLES').split(","))):
            pass
        else:
            payload={"content":"Only members with roles Commander,Lieutenant and Moderator can run this command."}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return

        DeployedList=await getDeployedList(903)

        if len(DeployedList)==20:
            options=[]
            for player in DeployedList:
                options.append({"label":player,"value":player})
                
            payload = {
                "content": "",
                "embeds":[
                    {
                    "title": "Deployer ID",
                    "description": json_data["member"]["user"]["id"],
                    "color": 65280,
                    
                  
                    "author": {
                        "name": json_data["member"]["user"]["username"],
                        
                        "icon_url": f'https://cdn.discordapp.com/avatars/{json_data["member"]["user"]["id"]}/{json_data["member"]["user"]["avatar"]}.png'
                    },
                    
                    "fields": [
                        {
                        "name": "Deploying",
                        "value": username,
                        "inline": "true"
                        }
                    ]
                    }
                ],
                "components": [
                    {
                    "type": 1,
                    "components": [
                        {
                        "type": 3,
                        "custom_id": "deploy",
                        "placeholder": "Choose a player to be undeployed:",
                        "min_values": 1,
                        "max_values": 1,
                        "options": options
                        }
                    ]
                    }
                ]
                }
         
        else:
            from ev import getClanData
            cd=await getClanData()
            deployed=[]
            for element in cd['field_deployed']:
                deployed.append(element['target_id'])
            
            UserID= UserData['uid'][0]['value']
            deployed.insert(0,UserID)
            status=await   deploy_new(deployed)
            if not status:
                payload={"content":"Whoops! That did not work, try again."}
                
            else:
                payload={"content":f"Deployed {username}"} 

        await send_followup(interaction_token=interaction_token, payload=payload)


commands = [SuperDeploy(),CheckPlayerStats(),CheckSurvivalScores(),GetCrosshair(),PeekSkins(),GetClanRanking(),GetClanRank(), Deploy(),ClanPlayersStatus(),LobbyLinks()]

