import requests
from google.cloud import bigquery
from datetime import datetime, timezone
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "key.json"
)

# BigQuery client
client = bigquery.Client(
    credentials=credentials,
    project="weather-dashboard-503407"
)

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
    "timestamp": datetime.now(timezone.utc).isoformat()
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