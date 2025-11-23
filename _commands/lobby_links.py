from . import send_followup
import httpx
from utils import (
    SlashCommand,
)

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
