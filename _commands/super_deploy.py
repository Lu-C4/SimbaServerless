from . import send_followup
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)
import os
from ev import getUserData,deploy_new,getDeployedList
class SuperDeploy(SlashCommand):
    def __init__(self):
        super().__init__(
            name="deploy",
            description="Deploy a player.",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to deploy",
                    required=True,
                )
            ]
        )

    async def respond(self, json_data: dict):
        
        interaction_token = json_data["token"]
        
        username = json_data["data"]["options"][0]["value"]
        UserData=await getUserData(username=username)
        if not UserData:
            payload={"content":"Player not found!"}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return
        
        roles=set(json_data['member']['roles'])

        if roles.intersection(set(os.environ.get('ALLOWED_ROLES').split(","))):
            pass
        else:
            payload={"content":"Only members with roles Commander,Lieutenant and Moderator can run this command."}
            await send_followup(interaction_token=interaction_token,payload=payload)
            return

        DeployedList=await getDeployedList(903)

        if len(DeployedList)==20:
            options=[]
            for player in DeployedList:
                options.append({"label":player,"value":player})
                
            payload = {
                "content": "",
                "embeds":[
                    {
                    "title": "Deployer ID",
                    "description": json_data["member"]["user"]["id"],
                    "color": 65280,
                    
                  
                    "author": {
                        "name": json_data["member"]["user"]["username"],
                        
                        "icon_url": f'https://cdn.discordapp.com/avatars/{json_data["member"]["user"]["id"]}/{json_data["member"]["user"]["avatar"]}.png'
                    },
                    
                    "fields": [
                        {
                        "name": "Deploying",
                        "value": username,
                        "inline": "true"
                        }
                    ]
                    }
                ],
                "components": [
                    {
                    "type": 1,
                    "components": [
                        {
                        "type": 3,
                        "custom_id": "deploy",
                        "placeholder": "Choose a player to be undeployed:",
                        "min_values": 1,
                        "max_values": 1,
                        "options": options
                        }
                    ]
                    }
                ]
                }
         
        else:
            from ev import getClanData
            cd=await getClanData()
            deployed=[]
            for element in cd['field_deployed']:
                deployed.append(element['target_id'])
            
            UserID= UserData['uid'][0]['value']
            deployed.insert(0,UserID)
            status=await   deploy_new(deployed)
            if not status:
                payload={"content":"Whoops! That did not work, try again."}
                
            else:
                payload={"content":f"Deployed {username}"} 

        print("Sending response back",payload)
        await send_followup(interaction_token=interaction_token, payload=payload)
        
