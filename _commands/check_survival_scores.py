from . import send_followup
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)
import discord
from ev import getUserData

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
