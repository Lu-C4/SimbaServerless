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


async def getEvUsername(discord_uid: int) -> str | None:
    """
    Returns the ev_username for a given Discord UID.
    Returns None if no matching user is found.
    """
    response = (
        supabase
        .table("verified_users")
        .select("ev_username")
        .eq("discord_uid", discord_uid)
        .maybe_single()
        .execute()
    )

    if response.data:
        return response.data.get("ev_username")

    return None

class CollectBounty(SlashCommand):

    def __init__(self):
        super().__init__(
            name="collectbounty",
            description="Collect some credits 🪙 for your kills ☠️!",
            
        )

    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        discordUID=json_data["member"]["user"]["id"]
        evUserName= await getEvUsername(discordUID)
        
        if not evUserName:
            payload={"content":f"You have not verified your account yet to collect bounty, please use /verify first."}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        data =  await getUserData(evUserName)
        
        if not data:
            payload = {"content": "Player data not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        
        field = data.get("field_kills", [])
        kills = field[0]["value"] if field else 0
            
        result=supabase.rpc("add_credits_if_more_kills", {
            "p_discord_uid": discordUID,
            "p_multiplication_factor": 3,
            "p_new_kills": kills
        }).execute()
        new_credits=result.data[0]['updated_credits']
        
        if result.data[0]['was_incremented']:
            payload={"content":f"You collected {result.data[0]['earned']} credits 🤑!\nYou now Have {new_credits} credits 💵."}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        else:
            payload={"content":f"You haven't made any new kills since your last collection!"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return