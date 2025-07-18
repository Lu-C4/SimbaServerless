from components import components
from utils import ComponentResponse

def get_fn(json_data: dict):
    for response_function in components:
        if response_function.name == json_data["data"]["custom_id"]:
            return response_function
    print("Not found")
    return None


class ComponentHandler(ComponentResponse):
    def __init__(self, json_data: dict):
        self.json_data = json_data

    async def execute(self):
        command = get_fn(self.json_data)
        if command is None:
            return None
        result = await command.respond(self.json_data)
        return result
