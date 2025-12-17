import httpx
async def text_input(interaction):
    url = f"https://discord.com/api/v10/interactions/{interaction['id']}/{interaction['token']}/callback"

    payload = {
        "type": 9,  # MODAL
        "data": {
            "custom_id": "namerecruit",
            "title": "Enter my name to recruit me!",
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 4,
                            "custom_id": "guess",
                            "label": "Name",
                            "style": 2,
                            "required": True
                        }
                    ]
                }
            ]
        }
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

import json
class Recruit():
    def __init__(self):
        self.name="namerecruit"
    async def respond(self,json_data):
        with open("sample2.json", "w", encoding="utf-8") as f:

            json.dump(json_data, f, indent=4, sort_keys=True)    
        return True
        
        

