from . import send_followup
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)

from ev import getUserData
import os
from supabase import create_client, Client


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def add_verified_user(ev_username: str, discord_uid: int, discord_username: str):
    data = {
        "ev_username": ev_username,
        "discord_uid": discord_uid,
        "discord_username": discord_username,
        
    }
    response = supabase.table("verified_users").insert(data).execute()
    print("=====")
    print(response)
    print("=====")
    
    return response.data



class Verify(SlashCommand):

    def __init__(self):
        super().__init__(
            name="verify",
            description="Verify and link your discord account to your ev.io account",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Your ev.io username",
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
        
            with open("tmp\\1.png", "rb") as f:
                a_bytes = f.read()

            with open("tmp\\2.png", "rb") as f:
                b_bytes = f.read()

            payload = {
                "content": (
                    f"## 🔐 Temporary Verification Required\n"
                    f"Your unique verification hash is:\n"
                    f"```\n{hash}\n```\n"
                    f"### 📋 What You Need To Do\n"
                    f"Please update your **ev.io** social bio to include the line:\n"
                    f"`hash = {hash}`\n\n"
                    f"### 🛠️ How To Update\n"
                    f"1. Go to **https://ev.io/user**\n"
                    f"2. Click the **Edit** button\n"
                    f"3. Scroll down to the **social_bio** field\n"
                    f"4. Paste the following code anywhere in the bio (You can change it back to whatever you wish once the verification is complete.):\n"
                    f"```\nhash = {hash}\n```\n"
                    f"5. Scroll further down and click **Save**\n\n"
                    
                ),
                "attachments": [
                    {"id": 0, "filename": "a.png"},
                    {"id": 1, "filename": "b.jpg"}
                ]
            }


            files_dict = {
                0: ("a.png", a_bytes, "image/png"),
                1: ("b.jpg", b_bytes, "image/jpeg")
            }

            await send_followup(interaction_token, payload, files_dict)

            return
        
        discordUID=json_data["member"]["user"]["id"]
        discord_username=json_data["member"]["user"]["username"]
        try:
            await add_verified_user(username,discordUID,discord_username)
            payload = {"content": f"You are Verie"}
        except Exception as e :
            payload={"content":"Error During verification, perhaps the account is already linked."}
            
        await send_followup(interaction_token=interaction_token, payload=payload)
