import httpx
import logging
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request, Response
from starlette.middleware import Middleware

from .utils import (
    InteractionType,
    InteractionResponseType,
    InteractionResponseFlags,
    CustomHeaderMiddleware,
)

app = FastAPI(
    middleware=[Middleware(CustomHeaderMiddleware)]
    )
logger = logging.getLogger(__name__)
DISCORD_TIMEOUT = httpx.Timeout(2.0, connect=1.0)


async def acknowledge_interaction(json_data: dict) -> None:
    callback_url = (
        f"https://discord.com/api/v10/interactions/"
        f"{json_data['id']}/{json_data['token']}/callback"
    )
    async with httpx.AsyncClient(timeout=DISCORD_TIMEOUT) as client:
        response = await client.post(
            callback_url,
            json={"type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE},
        )
        response.raise_for_status()


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

    handled = False

    async with httpx.AsyncClient() as client:

        # Slash commands
        if json_data["type"] == InteractionType.APPLICATION_COMMAND:
            from .core import CommandHandler

            handler = CommandHandler(json_data)
            handled = await handler.execute()

        # Message components (buttons, selects)
        elif json_data["type"] in (InteractionType.MESSAGE_COMPONENT, InteractionType.MODAL_SUBMIT):
            from .core import ComponentHandler
            handler = ComponentHandler(json_data)
            handled = await handler.execute()
         
            
            

        # Send handler result if present
        if not handled:
            # Fallback message
            response = await client.post(
                webhook_url,
                json={
                    "content": "Hmmm, I am not programmed to respond to that.The command could be temporarily disabled.",
                    "flags": InteractionResponseFlags.EPHEMERAL,
                },
            )
            response.raise_for_status()


@app.post("/interaction")
async def interactions(request: Request, background: BackgroundTasks):
    # Modals need immediate response
    json_data = await request.json()
    # 1️⃣ PING — respond immediately
    if json_data["type"] == InteractionType.PING:
        return {"type": InteractionResponseType.PONG}
    if json_data.get("data", {}).get("custom_id") == "recruit":
                from .modals import text_input
                await text_input(json_data)
                return None


    # Acknowledge through Discord before Lambda starts background processing.
    await acknowledge_interaction(json_data)
    background.add_task(process_interaction_safely, json_data)

    return Response(status_code=204)


async def process_interaction_safely(json_data: dict) -> None:
    try:
        await process_interaction(json_data)
    except Exception:
        logger.exception("Failed to process Discord interaction")


@app.post("/recruit")
async def recruit():
    from .recruit import sendSoldier
    await sendSoldier()
    return "Success",200
if __name__ == "__main__":
    uvicorn.run(app)
