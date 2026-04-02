from myctl.api import Plugin, Context, log
from .src.service import fetch_current_weather, fetch_forecast_weather

plugin = Plugin("weather")

DEFAULT_CITY = "Kolkata"


@plugin.command(path="current", help="Get current weather for a city")
async def get_current_weather(ctx: Context):
    city = ctx.args[0] if ctx.args else DEFAULT_CITY
    try:
        log.info(f"Fetching weather for {city}...")
        return ctx.ok(await fetch_current_weather(city))
    except Exception as e:
        log.error(f"Weather API error: {e}")
        return ctx.err(f"Could not find weather for '{city}'.")


@plugin.command(path="forecast", help="Get a 3-day weather forecast")
async def get_forecast(ctx: Context):
    city = ctx.args[0] if ctx.args else DEFAULT_CITY
    try:
        return ctx.ok(await fetch_forecast_weather(city))
    except Exception as e:
        log.error(f"Forecast error: {e}")
        return ctx.err(f"Failed to fetch forecast for '{city}'.")
