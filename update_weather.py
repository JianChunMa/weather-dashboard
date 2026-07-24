import requests
from google.cloud import bigquery
from datetime import datetime, timezone


# BigQuery client
client = bigquery.Client()


# Kuala Lumpur weather
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

weather = response.json()


row = {
    "city": "Kuala Lumpur",
    "temperature": weather["current"]["temperature_2m"],
    "humidity": weather["current"]["relative_humidity_2m"],
    "wind_speed": weather["current"]["wind_speed_10m"],
    "timestamp": datetime.now(timezone.utc)
}

#projectid + dataset + tablename
table_id = "weather-dashboard-503407.weather_dashboard.weather_data"


errors = client.insert_rows_json(
    table_id,
    [row]
)


if errors:
    print(errors)
else:
    print("Weather uploaded successfully")