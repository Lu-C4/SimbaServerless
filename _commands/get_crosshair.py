from . import send_followup
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)
from ev import getUserData


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
