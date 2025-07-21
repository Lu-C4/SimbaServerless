import os
import httpx
from ev import getUserData,deploy_new

async def edit_original_response( interaction_token: str, message_id: str, payload):
   url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}/messages/{message_id}"
   headers = {
    "Content-Type": "application/json"
    }

   async with httpx.AsyncClient() as client:
        response = client.patch(url, headers=headers, json=payload)

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


components=[Deploy()]