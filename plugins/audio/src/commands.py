async def get_status(sink_id: str) -> str:
    return f"Sink {sink_id} is currently at 50% volume."


async def set_volume(level: str) -> str:
    return f"Volume adjusted to {level}%"
