from myctl.api import registry, Request, ok

@registry.add_cmd("status", help="Get detailed sink status")
async def get_status(req: Request):
    """
    Get sink status.
    In V2.0, arguments are handled manually via req.args.
    """
    sink_id = req.args[0] if req.args else "0"
    return ok(f"Sink {sink_id} is currently at 50% volume.")

@registry.add_cmd("volume set", help="Change sink volume level")
async def volume_set(req: Request):
    """
    Set volume for a specific sink.
    Demonstrates nested sub-command routing.
    """
    level = req.args[0] if req.args else "0"
    return ok(f"Volume adjusted to {level}%")
