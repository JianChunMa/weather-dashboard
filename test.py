import requests
import json

url = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=3.1390"
    "&longitude=101.6869"
    "&current="
    "temperature_2m,"
    "relative_humidity_2m,"
    "wind_speed_10m"
)

response = requests.get(url)
response.raise_for_status()  # Raises an exception if the request fails

weather = response.json()

print(json.dumps(weather, indent=4))