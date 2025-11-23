import httpx
import os
import json

async def send_followup(interaction_token, payload, files_dict=None):
    """
    payload: dict for normal JSON (content, embeds, attachments)
    files_dict: {0: (filename, bytes, mime), 1: (...), ...}
    """
    url = f"https://discord.com/api/v10/webhooks/{os.environ['APPLICATION_ID']}/{interaction_token}"

    if not files_dict:
        async with httpx.AsyncClient() as client:
            return await client.post(url, json=payload)

    # Build multipart/form-data
    form = {
        "payload_json": (None, json.dumps(payload), "application/json")
    }

    for file_id, (filename, file_bytes, mime) in files_dict.items():
        form[f"files[{file_id}]"] = (filename, file_bytes, mime)

    async with httpx.AsyncClient() as client:
        return await client.post(url, files=form)
