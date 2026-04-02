from __future__ import annotations

from pulsectl_asyncio import PulseAsync
from pulsectl.pulsectl import PulseError, PulseIndexError


async def _resolve_sink(pulse: PulseAsync, sink_id: str):
    sink_key = sink_id.strip()
    if not sink_key or sink_key.lower() == "default":
        return await pulse.sink_default_get()

    if sink_key.isdigit():
        try:
            return await pulse.sink_info(int(sink_key))
        except PulseIndexError:
            pass

    try:
        return await pulse.get_sink_by_name(sink_key)
    except PulseIndexError:
        raise PulseIndexError(sink_key)


def _format_volume_percent(value: float) -> int:
    return max(0, min(100, int(round(value * 100))))


async def get_status(sink_id: str) -> str:
    async with PulseAsync("myctl-audio") as pulse:
        sink = await _resolve_sink(pulse, sink_id)
        percent = _format_volume_percent(sink.volume.value_flat)
        mute_state = "muted" if getattr(sink, "mute", False) else "unmuted"
        label = sink.description or sink.name
        return f"{label} ({sink.index}) is at {percent}% volume and is {mute_state}."


async def set_volume(sink_id: str, level: str) -> str:
    try:
        percent = int(level)
    except ValueError as exc:
        raise ValueError(f"invalid volume level: {level!r}") from exc

    if percent < 0 or percent > 100:
        raise ValueError("volume level must be between 0 and 100")

    async with PulseAsync("myctl-audio") as pulse:
        sink = await _resolve_sink(pulse, sink_id)
        await pulse.volume_set_all_chans(sink, percent / 100.0)
        refreshed = await pulse.sink_info(sink.index)
        return (
            f"Set {refreshed.description or refreshed.name} ({refreshed.index}) "
            f"to {_format_volume_percent(refreshed.volume.value_flat)}% volume."
        )
