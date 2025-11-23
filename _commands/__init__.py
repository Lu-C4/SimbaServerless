import httpx
import os
async def send_followup(interaction_token,payload):
    """Send the follow-up response after processing."""
    url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}"
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code!=200:
        print(response.text)