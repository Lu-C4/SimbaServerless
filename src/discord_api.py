import json
import os
from typing import Any

import httpx

DISCORD_API_URL = "https://discord.com/api/v10"
HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def send_followup(
    interaction_token: str,
    payload: dict[str, Any],
    files_dict: dict[int, tuple[str, bytes, str]] | None = None,
) -> httpx.Response:
    application_id = os.environ["APPLICATION_ID"]
    url = f"{DISCORD_API_URL}/webhooks/{application_id}/{interaction_token}"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        if not files_dict:
            response = await client.post(url, json=payload)
        else:
            form = {"payload_json": (None, json.dumps(payload), "application/json")}
            for file_id, (filename, file_bytes, mime) in files_dict.items():
                form[f"files[{file_id}]"] = (filename, file_bytes, mime)
            response = await client.post(url, files=form)
        response.raise_for_status()
        return response
