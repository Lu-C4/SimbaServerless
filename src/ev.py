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

# # # # # # # # # 
# LINK FETCHING #
# # # # # # # # #

import asyncio
import re

def extract_js_object(source, key):
    """Extract and convert a JavaScript object/array property to Python."""
   
    """Find an actual JS object property and parse its value."""

    

    # Find property declarations.
    pattern = (
        r'(?<![\w$])'
        + re.escape(key)
        + r'\s*:'
    )

    matches = list(re.finditer(pattern, source))

    if not matches:
        raise ValueError(f"{key!r} property not found")

    # Prefer the occurrence followed by an array literal.
    match = next(
        (
            m for m in matches
            if source[m.end():].lstrip().startswith("[")
        ),
        None
    )

    if match is None:
        raise ValueError(f"No array-valued {key!r} property found")

    source = source[match.end():]
    
    start = source.find(key)
    if start == -1:
        raise ValueError(f"{key!r} not found")

    start = source.find(":", start + len(key))
    if start == -1:
        raise ValueError("Property value not found")

    source = source[start + 1:]
    pos = 0

    def skip_ws():
        nonlocal pos
        while pos < len(source) and source[pos].isspace():
            pos += 1

    def parse_string():
        nonlocal pos
        quote = source[pos]
        pos += 1
        result = []

        while pos < len(source):
            c = source[pos]
            pos += 1

            if c == quote:
                return "".join(result)

            if c == "\\":
                if pos >= len(source):
                    raise ValueError("Unterminated escape")

                c = source[pos]
                pos += 1

                escapes = {
                    "n": "\n", "r": "\r", "t": "\t",
                    "b": "\b", "f": "\f",
                    "\\": "\\", "/": "/", 
                    "'": "'", '"': '"'
                }

                result.append(escapes.get(c, c))
            else:
                result.append(c)

        raise ValueError("Unterminated string")

    def parse_value():
        nonlocal pos
        skip_ws()

        if pos >= len(source):
            raise ValueError("Unexpected end of input")

        c = source[pos]

        if c in ("'", '"'):
            return parse_string()

        if c == "{":
            return parse_object()

        if c == "[":
            return parse_array()

        # Primitive value or unquoted identifier
        start = pos
        while pos < len(source) and source[pos] not in ",]} \t\r\n":
            pos += 1

        token = source[start:pos]

        if token == "true":
            return True
        if token == "false":
            return False
        if token == "null":
            return None

        try:
            return int(token) if token.isdigit() else float(token)
        except ValueError:
            return token

    def parse_key():
        nonlocal pos
        skip_ws()

        if source[pos] in ("'", '"'):
            return parse_string()

        start = pos
        while pos < len(source) and (
            source[pos].isalnum() or source[pos] in "_$"
        ):
            pos += 1

        if start == pos:
            raise ValueError(f"Invalid object key at position {pos}")

        return source[start:pos]

    def parse_object():
        nonlocal pos
        obj = {}
        pos += 1  # {

        while True:
            skip_ws()

            if pos >= len(source):
                raise ValueError("Unterminated object")

            if source[pos] == "}":
                pos += 1
                return obj

            key = parse_key()
            skip_ws()

            if source[pos] != ":":
                raise ValueError("Expected ':'")

            pos += 1
            obj[key] = parse_value()
            skip_ws()

            if source[pos] == ",":
                pos += 1
            elif source[pos] == "}":
                pos += 1
                return obj
            else:
                raise ValueError("Expected ',' or '}'")

    def parse_array():
        nonlocal pos
        arr = []
        pos += 1  # [

        while True:
            skip_ws()

            if pos >= len(source):
                raise ValueError("Unterminated array")

            if source[pos] == "]":
                pos += 1
                return arr

            arr.append(parse_value())
            skip_ws()

            if source[pos] == ",":
                pos += 1
            elif source[pos] == "]":
                pos += 1
                return arr
            else:
                raise ValueError("Expected ',' or ']'")

    return parse_value()


URL = "https://ev.io/dist/1-7-1/public/bundle.js?v=234553212"

MODES = [
    "social",
    "deathmatch",
    "deathmatch_fractal_earn",
    "deathmatch_earn",
    "instagib",
    "swords",
    "sniper_shotgun",
    "mayhem",
    "team_deathmatch",
    "infection",
    "team_deathmatch_earn",
    "last_man_standing",
    "last_team_standing",
    "last_team_standing_earn",
    "search_and_destroy",
    "survival",
    "survival_earn",
    "capture_the_flag",
]


async def get_matchmaker_regions(client):
    response = await client.get(URL)
    response.raise_for_status()

    return extract_js_object(response.text, "matchmakerRegions")


async def get_lobby_id(client, region, mode, semaphore):
    async with semaphore:
        url = f"{region['httpUrl']}/matchmaker/rooms"

        try:
            response = await client.post(
                url,
                json={
                    "regionId": region["id"],
                    "isPublic": True,
                    "params": {"gameModeId": mode}
                }
            )
            response.raise_for_status()

            data = response.json()
            return mode, f"https://ev.io/game={data['id']}"

        except httpx.ConnectError as e:
            print(f"Connection failed: {url} | {e}")
            return mode, None

async def get_lobby_links():
    MAX_CONCURRENT = 50

    limits = httpx.Limits(
        max_connections=MAX_CONCURRENT + 5,
        max_keepalive_connections=MAX_CONCURRENT
    )

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"},
        limits=limits,
        http2=True
    ) as client:

        regions = await get_matchmaker_regions(client)

        async def process_region(region):
            tasks = [
                get_lobby_id(client, region, mode, semaphore)
                for mode in MODES
            ]

            results = await asyncio.gather(*tasks)

            return {
                region["id"]: [
                    {mode: link}
                    for mode, link in results
                ]
            }

        links = await asyncio.gather(
            *(process_region(region) for region in regions)
        )

        return links
