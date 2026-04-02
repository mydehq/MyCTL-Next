import httpx


async def fetch_current_weather(city: str):
    url = f"https://wttr.in/{city}?format=j1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

    current = data["current_condition"][0]
    temp_c = current["temp_C"]
    desc = current["weatherDesc"][0]["value"]
    humidity = current["humidity"]
    wind_speed = current["windspeedKmph"]

    return {
        "city": city,
        "temperature": f"{temp_c}°C",
        "condition": desc,
        "humidity": f"{humidity}%",
        "wind_speed": f"{wind_speed} km/h",
        "source": "wttr.in",
    }


async def fetch_forecast_weather(city: str):
    url = f"https://wttr.in/{city}?format=j1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

    forecasts = []
    for day in data["weather"]:
        date = day["date"]
        max_temp = day["maxtempC"]
        min_temp = day["mintempC"]
        desc = day["hourly"][4]["weatherDesc"][0]["value"]

        forecasts.append(
            {
                "date": date,
                "max": f"{max_temp}°C",
                "min": f"{min_temp}°C",
                "condition": desc,
            }
        )

    return {
        "city": city,
        "forecast": forecasts,
        "source": "wttr.in",
    }
