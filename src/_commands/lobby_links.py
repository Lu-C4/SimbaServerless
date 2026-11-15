from . import send_followup
from ..utils import SlashCommand
from ..ev import get_lobby_links


class LobbyLinks(SlashCommand):

    def __init__(self):
        super().__init__(
            name="gamelinks",
            description="Get a list of links for all active lobbies.",
            options=[],
        )

    async def respond(self, json_data: dict):

        interaction_token = json_data["token"]

        # ---------------------------
        # Fetch lobby information
        # ---------------------------

        links= await get_lobby_links()
        
        # ---------------------------
        # Send
        # ---------------------------
        
        PRIORITY_MODES = {
            "deathmatch_earn",
            "survival_earn",
            "deathmatch",
            "survival",
            "swords",
            "sniper_shotgun",
        }

        DISCORD_LIMIT = 2000


        def format_mode(mode):
            return mode.replace("_", " ").title()


        def chunk_discord_message(lines, limit=DISCORD_LIMIT):
            """Split lines into Discord messages without exceeding the limit."""
            chunks = []
            current = ""

            for line in lines:
                # Account for the newline between lines.
                separator = "\n" if current else ""
                candidate = current + separator + line

                if len(candidate) > limit:
                    if current:
                        chunks.append(current)
                        current = line
                    else:
                        raise ValueError(
                            f"Single line exceeds Discord limit: {len(line)} characters"
                        )
                else:
                    current = candidate

            if current:
                chunks.append(current)

            return chunks


        def generate_discord_messages(links):
            priority_lines = []
            remaining_lines = []

            for region_data in links:
                region, games = next(iter(region_data.items()))

                priority_lines.append(f"### {region.upper()}")
                remaining_lines.append(f"### {region.upper()}")

                for game in games:
                    mode, url = next(iter(game.items()))

                    line = f"• [{format_mode(mode)}]({url})"

                    if mode in PRIORITY_MODES:
                        priority_lines.append(line)
                    else:
                        remaining_lines.append(line)

                priority_lines.append("")
                remaining_lines.append("")

            return (
                chunk_discord_message(priority_lines),
                chunk_discord_message(remaining_lines)
            )


        # Generate messages
        priority_messages, remaining_messages = generate_discord_messages(links)

        for message in remaining_messages:
                    await send_followup(
                        interaction_token=interaction_token,
                        payload={"content": message}
                    )
                
        for message in priority_messages:
            await send_followup(
                interaction_token=interaction_token,
                payload={"content": message}
            )
            
        return