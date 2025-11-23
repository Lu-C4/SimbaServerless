MULTIPLICATION_FACTOR=3

from . import send_followup
from utils import (
    SlashCommand,
)

from ev import getUserData
import os
from supabase import create_client, Client


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def getCredits(discord_uid: int) -> str | None:
    """
    Returns the number of credits for a given Discord UID.
    Returns None if no matching user is found.
    """
    
    response = (
        supabase
        .table("credits")
        .select("credits")
        .eq("discord_uid", discord_uid)
        .maybe_single()
        .execute()
    )
    print(response)

    if response.data:
        return response.data.get("credits")

    return None

class Credits(SlashCommand):

    def __init__(self):
        super().__init__(
            name="credits",
            description="See how many credits you have.",
            
        )

    async def respond(self, json_data: dict):
        try:
            
            if "member" in json_data:
                discordUID = int(json_data["member"]["user"]["id"])
            elif "user" in json_data:
                discordUID = int(json_data["user"]["id"])
            interaction_token = json_data["token"]
            
            credits = await getCredits(discordUID)
            
            if not credits:
                payload={"content":f"You have not earned any credits,use /collectbounty to earn some! 🤑."}
                await send_followup(interaction_token=interaction_token, payload=payload)
                return
            
            else:
                payload={"content":f"You have {credits} credits! 🤑."}
                await send_followup(interaction_token=interaction_token, payload=payload)
                return
        except Exception as e:
            print(e)