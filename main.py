import uvicorn
import requests
from fastapi import FastAPI, Request
from starlette.middleware import Middleware
from utils import (
    InteractionType,
    InteractionResponseType,
    InteractionResponseFlags,
    CustomHeaderMiddleware,
)


app = FastAPI(middleware=[Middleware(CustomHeaderMiddleware)])


@app.post("/interactions")
async def interactions(request: Request):
    json_data = await request.json()

    if json_data["type"] == InteractionType.PING:
        # A ping test sent by discord to check if your server works
        return {"type": InteractionResponseType.PONG}
    #defer response assuming it's a command
    
    payload = {"type": 5}  # 5 = DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    headers = {"Content-Type": "application/json"}
    interaction_token = json_data["token"]
    interaction_id = json_data["id"]
    url = f"https://discord.com/api/v10/interactions/{interaction_id}/{interaction_token}/callback"
    requests.post(url, json=payload, headers=headers)
    from core import CommandHandler
    if json_data["type"] == InteractionType.APPLICATION_COMMAND:
        # We only want to handle slash commands
        handler = CommandHandler(json_data)
        result = await handler.execute()
        if result is not None:
            return result

    # No result means either the command is not found or the command is not registered
    # Or you havent implemented the command yet
    # Or you forgot to return the result
    # Or idk just check it man i cant do everything for you

    return {
        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "content": "Hello Buddy, This is a by default message for any unrecognized interaction.",
            "flags": InteractionResponseFlags.EPHEMERAL,
        },
    }


if __name__ == "__main__":
    uvicorn.run(app)
