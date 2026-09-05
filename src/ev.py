import httpx

async def getUserData(username:str):
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://ev.io/stats-by-un/{username}", timeout=30)
        if response.status_code != 200:
            return None
        data = response.json()
        return data[0] if data else None
    
async def fetch_csrf_tokens(client):
    """Fetches CSRF tokens required for clan edit form submission."""
    from lxml import html
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
    
async def deploy_new(field_deployed_values:list):
    """
    Deploys players from a list of UIDs, assumes KEY and VALUE are the env variables 
    for the cookies required to make the changes.
    Form data is hardcoded into the function
    
    :param field_deployed_values: list of UIDS
    :return: True if successful, False if not.
    :rtype: bool
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    COOKIES={os.environ.get("KEY") : os.environ.get("VALUE") }
    
    async with httpx.AsyncClient(cookies=COOKIES) as client:
        form_build_id, form_token = await fetch_csrf_tokens(client)
        if not form_build_id or not form_token:
            print("Failed to retrieve CSRF tokens. Aborting.")
            return False

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
            "field_discord_link[0][uri]": "https://discord.gg/qDgwWGRQ",
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
            if response.status_code!=303:
                print(f"Error submitting form: {e}")
                return False
        return True

async def getDeployedList(UID=903):
    """Get list of USERNAMES of deployed members in a clan by it's UID"""
    from lxml import html

    async with httpx.AsyncClient() as client:
        response=await client.get(f"https://ev.io/group/{UID}/")
        tree=html.fromstring(response.text)
        matches=tree.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "field--label-above", " " ))]')
        return [match.text_content() for match in matches[0][1]]
    
async def getUserDataByID(UID):
    async with httpx.AsyncClient() as client:
        response=await client.get(f"https://ev.io/user/{UID}?_format=json")
        if response.status_code != 200:
            return None
        data = response.json()
        return data if data else None
    
async def getUserNameByID(UID):
    data= await getUserDataByID(UID)
    return data['name'][0]['value']

async def getClanData(UID=903):
    async with httpx.AsyncClient() as client:
        data= (await client.get(f"https://ev.io/group/{UID}?_format=json"))
    return data.json()

