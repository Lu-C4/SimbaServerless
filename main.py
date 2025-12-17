import uvicorn
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from starlette.middleware import Middleware

from utils import (
    InteractionType,
    InteractionResponseType,
    InteractionResponseFlags,
    CustomHeaderMiddleware,
)

app = FastAPI(middleware=[Middleware(CustomHeaderMiddleware)])


async def process_interaction(json_data: dict):
    """
    Runs AFTER the interaction has been ACKed.
    Sends responses using webhook follow-ups.
    """
    interaction_token = json_data["token"]
    application_id = json_data["application_id"]

    webhook_url = (
        f"https://discord.com/api/v10/webhooks/"
        f"{application_id}/{interaction_token}"
    )

    result = None  

    async with httpx.AsyncClient() as client:

        # Slash commands
        if json_data["type"] == InteractionType.APPLICATION_COMMAND:
            from core import CommandHandler

            handler = CommandHandler(json_data)
            result = await handler.execute()

        # Message components (buttons, selects)
        elif json_data["type"] == InteractionType.MESSAGE_COMPONENT or json_data["type"]==InteractionType.MODAL_SUBMIT:
            from core import ComponentHandler
            handler = ComponentHandler(json_data)
            result = await handler.execute()
         
            
            

        # Send handler result if present
        if result:
            await client.post(webhook_url, json=result)
        else:
            import json
            with open("sample2.json", "w", encoding="utf-8") as f:

                json.dump(json_data, f, indent=4, sort_keys=True)
            # Fallback message
            await client.post(
                webhook_url,
                json={
                    "content": "Hmmm, I am not programmed to respond to that.The command could be temporarily disabled.",
                    "flags": InteractionResponseFlags.EPHEMERAL,
                },
            )


@app.post("/interactions")
async def interactions(request: Request, background: BackgroundTasks):
    # Modals need immediate response
    json_data = await request.json()
    if json_data.get('data').get('custom_id')=="recruit":
                
                from modals import text_input
                await text_input(json_data)
                return 

    # 1️⃣ PING — respond immediately
    if json_data["type"] == InteractionType.PING:
        return {"type": InteractionResponseType.PONG}

    # 2️⃣ ACK immediately (DEFER)
    background.add_task(process_interaction, json_data)

    return {
        "type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    }

@app.post("/recruit")
async def recruit():
    from recruit import sendSoldier
    await sendSoldier()
    return "Success",200
if __name__ == "__main__":
    uvicorn.run(app)
