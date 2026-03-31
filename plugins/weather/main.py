import httpx
from myctl.api import registry, ok, err, Request, logger

# Default city if none provided
DEFAULT_CITY = "Kolkata"

@registry.add_cmd(path="current", help="Get current weather for a city")
async def get_current_weather(req: Request):
    """
    Fetches current weather data from wttr.in (JSON format).
    Usage: myctl weather current [city]
    """
    city = req.args[0] if req.args else DEFAULT_CITY
    url = f"https://wttr.in/{city}?format=j1"

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching weather for {city}...")
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            current = data["current_condition"][0]
            temp_c = current["temp_C"]
            desc = current["weatherDesc"][0]["value"]
            humidity = current["humidity"]
            wind_speed = current["windspeedKmph"]

            # Format a nice dictionary for the Client to render as JSON
            result = {
                "city": city,
                "temperature": f"{temp_c}°C",
                "condition": desc,
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind_speed} km/h",
                "source": "wttr.in"
            }
            return ok(result)

    except httpx.HTTPStatusError as e:
        logger.error(f"Weather API error: {e}")
        return err(f"Could not find weather for '{city}'.")
    except Exception as e:
        logger.error(f"Unexpected error in weather plugin: {e}")
        return err("Failed to fetch weather data.")

@registry.add_cmd(path="forecast", help="Get a 3-day weather forecast")
async def get_forecast(req: Request):
    """
    Fetches weather forecast from wttr.in.
    Usage: myctl weather forecast [city]
    """
    city = req.args[0] if req.args else DEFAULT_CITY
    url = f"https://wttr.in/{city}?format=j1"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            forecasts = []
            for day in data["weather"]:
                date = day["date"]
                max_temp = day["maxtempC"]
                min_temp = day["mintempC"]
                # Get noon weather description
                desc = day["hourly"][4]["weatherDesc"][0]["value"]
                
                forecasts.append({
                    "date": date,
                    "max": f"{max_temp}°C",
                    "min": f"{min_temp}°C",
                    "condition": desc
                })

            return ok({
                "city": city,
                "forecast": forecasts,
                "source": "wttr.in"
            })

    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return err(f"Failed to fetch forecast for '{city}'.")
