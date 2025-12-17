import os
import httpx
from ev import getUserData,deploy_new
import time
from supabase import create_async_client, AsyncClient
import zlib
import base64


ENCRYPT_KEY=os.environ.get("ENCRYPT_KEY")
KEY = bytes.fromhex(ENCRYPT_KEY)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  

def xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def decrypt(code: str) -> str:
    encrypted = base64.b85decode(code.encode())
    compressed = xor(encrypted, KEY)
    return zlib.decompress(compressed).decode()
        
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
        res= await client.post(url, files=form)
        
        
        
async def edit_original_response( interaction_token: str, message_id: str, payload):
   url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}/messages/{message_id}"
   headers = {
    "Content-Type": "application/json"
    }

   async with httpx.AsyncClient() as client:
        response = await client.patch(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Failed to edit message: {response.status_code}")
            print(response.text)


class Deploy():
    def __init__(self):
        self.name="deploy"
    async def respond(self,json_data):
        
        interaction_token = json_data["token"]

        if json_data["member"]["user"]["id"] != json_data["message"]["embeds"][0]["description"]:
            # silently delete
            async with httpx.AsyncClient() as client:
                await client.delete(
                f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}/messages/@original",
                headers={"Authorization": f"Bot {os.environ.get('TOKEN')}"}
                )
            return
        PlayerToDeploy=json_data['message']['embeds'][0]['fields'][0]['value']
        PlayerToUndeploy=json_data['data']['values'][0]
        
        UIDPlayerToDeploy=(await getUserData(username=PlayerToDeploy))['uid'][0]['value']
        UIDPlayerToUndeploy=(await getUserData(username=PlayerToUndeploy))['uid'][0]['value']
        
        from ev import getClanData
        cd=await getClanData()
        deployed=[]
        for element in cd['field_deployed']:
            deployed.append(element['target_id'])
        deployed.remove(UIDPlayerToUndeploy)
        deployed.insert(0,UIDPlayerToDeploy)
        status=await deploy_new(deployed)
        if not status:
            payload = {
            "content": f"Whoops! That did not work, try again.",
            "components": []
            }
        else:       
            payload = {
            "content": f"Deployed {PlayerToDeploy} instead of {PlayerToUndeploy}!",
            "components": []
            }

        await edit_original_response(interaction_token=interaction_token,message_id=json_data["message"]["id"],payload=payload)
        
        #delete the follow up message 
        async with httpx.AsyncClient() as client:
            await client.delete(
            f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}/messages/@original",
            headers={"Authorization": f"Bot {os.environ.get('TOKEN')}"}
            )

# Modal
import json
async def append_skin(
    discord_id: int,
    skin: str
) -> None:
    """
    Append a single skin string to inventory.
    Creates row if it does not exist.
    """

    supabase: AsyncClient = await create_async_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

    response = await supabase.rpc(
        "upsert_append_inventory",
        {
            "p_discord_id": discord_id,
            "p_skin": skin
        }
    ).execute()
    
async def disable_button_by_event(channel_id, message_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"

    headers = {
        "Authorization": f"Bot {os.environ.get('TOKEN')}",
        "Content-Type": "application/json"
    }

    payload = {
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 1,
                        "label": "Recruit",
                        "custom_id": "open_text_modal",
                        "disabled": True
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        await client.patch(url, headers=headers, json=payload)

        
class Recruit():
    def __init__(self):
        self.name="namerecruit"
    async def respond(self,json_data):
        interaction_token=json_data["token"]
        meta=json_data['message']['content'].split("\n")[1].strip("||")
        timeStamp,name,tier=decrypt(meta).split("$$")
        if time.time()-float(timeStamp)>20*60 :
            print("It is too late")
            payload={
                "content":"Ooops! It's been more than 20 minutes, the soldier left!"
            }
            await send_followup(
            interaction_token=interaction_token,
            payload=payload
            )
            
            msg = json_data["message"]

            delete_url = (
                f"https://discord.com/api/v10/channels/"
                f"{msg['channel_id']}/messages/{msg['id']}"
            )

            headers = {
                "Authorization": f"Bot {os.environ.get('TOKEN')}"
            }

            async with httpx.AsyncClient() as client:
                await client.delete(delete_url, headers=headers)
            
            return True
        elif json_data['data']['components'][0]['components'][0]['value']!=name:
            payload={
                "content":"Wrong Guess!"
            }
        
        else:
            await append_skin(
                discord_id=json_data['member']['user']['id'],
                skin=meta
            )
            message_id=json_data['message']['id']
            channel_id=json_data['channel']['id']
            await disable_button_by_event(channel_id=channel_id,message_id=message_id)
            

            payload={
            "content":f"{json_data['member']['user']['global_name']}, you have recruited {name}, a {tier} tier soldier!"
            }    
        
            
        
        await send_followup(
            interaction_token=interaction_token,
            payload=payload
            )
        return True
        
         
        
        

components=[Deploy(),Recruit()]