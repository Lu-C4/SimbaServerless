from . import send_followup
from lxml import html
import httpx
from utils import (
    SlashCommand,
)

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
