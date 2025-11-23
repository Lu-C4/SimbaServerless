from . import send_followup
from lxml import html
import httpx
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)


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
