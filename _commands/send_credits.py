from . import send_followup
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)
from supabase import create_client
import os

MULTIPLICATION_FACTOR = 3

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def getCredits(discord_uid: int) -> int:
    """Get current credits for a user. Returns 0 if user doesn't exist."""
    print("DISCORD UIDDDDDDD",discord_uid)
    response = (
        supabase
        .table("credits")
        .select("credits")
        .eq("discord_uid", discord_uid)
        .maybe_single()
        .execute()
    )
    if not response:
        return 0
    if response.data and response.data.get("credits") is not None:
        return response.data["credits"]
    return 0


async def updateCredits(discord_uid: int, new_credits: int):
    """
    Upsert credits for a user.
    If the discord_uid doesn't exist, it will create a new row automatically.
    """
    supabase.table("credits").upsert(
        {"discord_uid": discord_uid, "credits": new_credits}, on_conflict="discord_uid"
    ).execute()


class SendCredits(SlashCommand):
    def __init__(self):
        super().__init__(
            name="sendcredits",
            description="Send some of your credits to another user.",
            options=[
                Option(
                    name="recipient",
                    description="User to send credits to",
                    type=ApplicationCommandOptionType.USER,
                    required=True,
                ),
                Option(
                    name="amount",
                    description="Number of credits to send",
                    type=ApplicationCommandOptionType.INTEGER,
                    required=True,
                ),
            ],
        )

    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        if "member" in json_data:
            sender_uid = int(json_data["member"]["user"]["id"])
        elif "user" in json_data:
            sender_uid = int(json_data["user"]["id"])
        
        
        options = {opt["name"]: opt["value"] for opt in json_data["data"]["options"]}

        recipient_uid = int(options["recipient"])
        amount = int(options["amount"])

        if amount <= 0:
            payload = {"content": "❌ You must send a positive number of credits."}
            await send_followup(interaction_token, payload)
            return

        if recipient_uid == sender_uid:
            payload = {"content": "❌ You cannot send credits to yourself."}
            await send_followup(interaction_token, payload)
            return

        sender_credits = await getCredits(sender_uid)
        if sender_credits < amount:
            payload = {"content": f"❌ You only have {sender_credits} credits."}
            await send_followup(interaction_token, payload)
            return

        # Deduct from sender
        await updateCredits(sender_uid, sender_credits - amount)

        # Add to recipient (creates new row if recipient doesn't exist)
        recipient_credits = await getCredits(recipient_uid)
        await updateCredits(recipient_uid, recipient_credits + amount)

        payload = {
            "content": f"✅ Sent {amount} credits to <@{recipient_uid}>!\nYou now have {sender_credits - amount} credits left."
        }
        await send_followup(interaction_token, payload)
