from . import send_followup
from utils import (
    SlashCommand,
    Option,
    ApplicationCommandOptionType,
)

from ev import getUserData,deploy_new,getUserNameByID

class Deploy(SlashCommand):

    def __init__(self):
        super().__init__(
            name="self_deploy",
            description="Deploy yourself!",
            options=[
                Option(
                    name="username",
                    type=ApplicationCommandOptionType.STRING,
                    description="Username to deploy",
                    required=True,
                )
            ],
        )

    async def respond(self, json_data: dict):
        interaction_token = json_data["token"]
        username = json_data["data"]["options"][0]["value"]
        data =  await getUserData(username)
        
        if not data:
            payload = {"content": "Player not found\n*Roar?*"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        import hashlib
        hash=hashlib.sha256(f'{json_data["member"]["user"]["id"]}Samael{username}'.encode()).hexdigest()
        if  not (data['field_social_bio']) or  (hash) not in data['field_social_bio'][0]['value'] :
            payload = {"content": f"Please modify your ev.io social_bio to include {hash}\nhttps://ev.io/user/<your_user_ID>/edit"}
            await send_followup(interaction_token=interaction_token, payload=payload)
            return
        from ev import getClanData
        cd= await getClanData()
        deployed=[]
        for element in cd['field_deployed']:
            deployed.append(element['target_id'])
        
        if len(deployed)==20:
            undeployed=deployed.pop()
            payload = {"content": f"Deployed **{username}** instead of  **{ await getUserNameByID(undeployed)}**!" }
        else:
            payload={"content": f"Deployed {username}!"}
        
        deployed.insert(0,data["uid"][0]["value"])
        
        status = await deploy_new(deployed)
        
        if not status:
            payload={"content":"Whoops! That did not work!\nTry again or contact a Commander , Lieutenant or a Moderator and ask them to use /deploy"}
            
        
        await send_followup(interaction_token=interaction_token, payload=payload)
