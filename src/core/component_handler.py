from ..components import components
from ..utils import ComponentResponse

def get_fn(json_data: dict):
    return components.get(json_data["data"]["custom_id"])


class ComponentHandler(ComponentResponse):
    def __init__(self, json_data: dict):
        self.json_data = json_data

    async def execute(self):
        command = get_fn(self.json_data)
        if command is None:
            return None
        await command.respond(self.json_data)
        return True
