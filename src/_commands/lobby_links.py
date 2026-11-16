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

        DISCORD_LIMIT = 4000
        COMPONENT_LIMIT = 40
        COMPONENTS_V2 = 1 << 15

        PRIORITY_MODES = {
            "deathmatch_earn",
            "survival_earn",
            "deathmatch",
            "survival",
            "swords",
            "sniper_shotgun",
        }


        def format_mode(mode):
            return mode.replace("_", " ").title()


        def build_region_container(region, games, selected_modes=None):
            """Build one visually grouped container for a region."""

            lines = [f"### {region.upper()}"]

            for game in games:
                mode, url = next(iter(game.items()))

                if selected_modes is not None and mode not in selected_modes:
                    continue

                lines.append(f"• [{format_mode(mode)}]({url})")

            if len(lines) == 1:
                return None

            return {
                "type": 17,  # Container
                "components": [
                    {
                        "type": 10,  # Text Display
                        "content": "\n".join(lines)
                    }
                ]
            }


        def generate_component_payloads(links, selected_modes=None):
            """Build and chunk Components V2 payloads."""

            payloads = []
            components = []
            text_length = 0

            def flush():
                nonlocal components, text_length

                if not components:
                    return

                payloads.append({
                    "flags": COMPONENTS_V2,
                    "components": components
                })

                components = []
                text_length = 0

            for region_data in links:
                region, games = next(iter(region_data.items()))

                container = build_region_container(
                    region,
                    games,
                    selected_modes
                )

                if container is None:
                    continue

                content_length = len(
                    container["components"][0]["content"]
                )

                # Each region container has 2 components:
                # Container + Text Display.
                if (
                    text_length + content_length > DISCORD_LIMIT
                    or len(components) + 2 > COMPONENT_LIMIT
                ):
                    flush()

                components.append(container)
                text_length += content_length

            flush()

            return payloads


        def generate_messages(links):
            priority = generate_component_payloads(
                links,
                PRIORITY_MODES
            )

            remaining = generate_component_payloads(
                links,
                None
            )

            # Remove priority modes from the second set.
            remaining = generate_component_payloads(
                links,
                set(
                    mode
                    for region in links
                    for game in next(iter(region.values()))
                    for mode in game
                ) - PRIORITY_MODES
            )

            return priority, remaining

        
        def generate_messages(links):
            all_modes = {
                mode
                for region in links
                for game in next(iter(region.values()))
                for mode in game
            }

            priority = generate_component_payloads(
                links,
                PRIORITY_MODES
            )

            remaining = generate_component_payloads(
                links,
                all_modes - PRIORITY_MODES
            )

            return priority, remaining


        # Generate payloads
        priority, remaining = generate_messages(links)

        async def publish_lobbies(interaction_token):
            for payload in remaining:
                await send_followup(interaction_token, payload)

            for payload in priority:
                await send_followup(interaction_token, payload)

        await publish_lobbies(interaction_token=interaction_token)