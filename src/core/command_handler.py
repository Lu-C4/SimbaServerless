from ..commands import commands
from ..discord_api import send_followup

def get_command(json_data: dict):
    return commands.get(json_data["data"]["name"])


class CommandHandler:
    def __init__(self, json_data: dict):
        self.json_data = json_data

    async def execute(self):
        command = get_command(self.json_data)
        if command is None:
            return False
        
        try:
            await command.respond(self.json_data)
        except Exception :
            await send_followup(
                
                self.json_data.get('token'),
                {
                    
                    "content" : "An error occured while handling that command!"
                 
                }
                
            )
        return True
