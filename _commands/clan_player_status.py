from . import send_followup
from utils import (
    SlashCommand,
)
import os

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
