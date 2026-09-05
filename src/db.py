import asyncio
from typing import Any


async def execute_sync(query: Any) -> Any:
    """Run the synchronous Supabase query client without blocking the event loop."""
    return await asyncio.to_thread(query.execute)
