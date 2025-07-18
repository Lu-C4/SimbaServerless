import os
import httpx
import requests
from lxml import html
async def edit_original_response( interaction_token: str, message_id: str, payload):
   url = f"https://discord.com/api/v10/webhooks/{os.environ.get('APPLICATION_ID')}/{interaction_token}/messages/{message_id}"
   headers = {
    "Content-Type": "application/json"
    }



   with httpx.Client() as client:
        response = client.patch(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Failed to edit message: {response.status_code}")
            print(response.text)

async def getUserData(username):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://ev.io/stats-by-un/{username}", timeout=30)
        if response.status_code != 200:
            return None
        data = response.json()
        return data[0] if data else None
async def fetch_csrf_tokens(client):
    """Fetches CSRF tokens required for form submission."""
    try:
        response = await client.get("https://ev.io/group/903/edit")
        response.raise_for_status()
        
        tree = html.fromstring(response.text)
        form_build_id = tree.xpath("//input[@name='form_build_id']/@value")[0]
        form_token = tree.xpath("//input[@name='form_token']/@value")[0]

        return form_build_id, form_token
    except Exception as e:
        print(f"Error fetching CSRF tokens: {e}")
        return None, None
async def deploy_new(field_deployed_values):
    from dotenv import load_dotenv
    load_dotenv()
    COOKIES={os.environ.get("KEY") : os.environ.get("VALUE") }
    """Submits form data asynchronously."""
    async with httpx.AsyncClient(cookies=COOKIES) as client:
        form_build_id, form_token = await fetch_csrf_tokens(client)
        if not form_build_id or not form_token:
            print("Failed to retrieve CSRF tokens. Aborting.")
            return

        # Form Data
        form_data = {
            "label[0][value]": "The Assassins",
            "form_build_id": form_build_id,
            "form_token": form_token,
            "form_id": "group_clan_edit_form",
            "field_insignia[0][fids]": "10364",
            "field_insignia[0][display]": "1",
            "field_banner[0][fids]": "94990",
            "field_banner[0][display]": "1",
            "field_motto[0][value]": "Fear not the darkness, But welcome its Embrace",
            "field_discord_link[0][uri]": "https://discord.gg/sSGzVXP6Fy",
            "op": "Save"
        }

        # Add deployed values dynamically
        for value in field_deployed_values:
            form_data[f"field_deployed[{value}]"] = str(value)

        # Convert to multipart
        files = {key: (None, value) for key, value in form_data.items()}

        try:
            response = await client.post("https://ev.io/group/903/edit", files=files)
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Error submitting form: {e}")






class Deploy():
    def __init__(self):
        self.name="deploy"
    async def respond(self,json_data):
        
        interaction_token = json_data["token"]
        PlayerToDeploy=json_data['message']['content'][10:]
        PlayerToUndeploy=json_data['data']['values'][0]
        
        UIDPlayerToDeploy=(await getUserData(username=PlayerToDeploy))['uid'][0]['value']
        UIDPlayerToUndeploy=(await getUserData(username=PlayerToUndeploy))['uid'][0]['value']
        

        cd=requests.get("https://ev.io/group/903?_format=json").json()
        deployed=[]
        for element in cd['field_deployed']:
            deployed.append(element['target_id'])
        deployed.remove(UIDPlayerToUndeploy)
        deployed.insert(0,UIDPlayerToDeploy)
        await deploy_new(deployed)
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