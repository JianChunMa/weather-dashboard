import requests
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timezone
import os

print("Current directory:", os.getcwd())
print("Key exists:", os.path.exists("key.json"))

# -------------------------
# Authentication
# -------------------------
credentials = service_account.Credentials.from_service_account_file(
    "key.json"
)

client = bigquery.Client(
    credentials=credentials,
    project="weather-dashboard-503407"
)


locations = [
    {"state": "Johor", "city": "Johor Bahru", "lat": 1.4927, "lon": 103.7414},
    {"state": "Kedah", "city": "Alor Setar", "lat": 6.1248, "lon": 100.3678},
    {"state": "Kelantan", "city": "Kota Bharu", "lat": 6.1254, "lon": 102.2386},
    {"state": "Melaka", "city": "Melaka City", "lat": 2.1896, "lon": 102.2501},
    {"state": "Negeri Sembilan", "city": "Seremban", "lat": 2.7297, "lon": 101.9381},
    {"state": "Pahang", "city": "Kuantan", "lat": 3.8077, "lon": 103.3260},
    {"state": "Perak", "city": "Ipoh", "lat": 4.5975, "lon": 101.0901},
    {"state": "Perlis", "city": "Kangar", "lat": 6.4414, "lon": 100.1986},
    {"state": "Penang", "city": "George Town", "lat": 5.4141, "lon": 100.3288},
    {"state": "Sabah", "city": "Kota Kinabalu", "lat": 5.9804, "lon": 116.0735},
    {"state": "Sarawak", "city": "Kuching", "lat": 1.5533, "lon": 110.3592},
    {"state": "Selangor", "city": "Shah Alam", "lat": 3.0738, "lon": 101.5183},
    {"state": "Terengganu", "city": "Kuala Terengganu", "lat": 5.3302, "lon": 103.1408},
    {"state": "Kuala Lumpur", "city": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869},
    {"state": "Putrajaya", "city": "Putrajaya", "lat": 2.9264, "lon": 101.6964},
    {"state": "Labuan", "city": "Victoria", "lat": 5.2831, "lon": 115.2308},
]

# -------------------------
# Weather API
# -------------------------
url = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=3.1390"
    "&longitude=101.6869"
    "&current="
    "temperature_2m,"
    "relative_humidity_2m,"
    "wind_speed_10m"
    "&timezone=Asia/Kuala_Lumpur"
)

response = requests.get(url)
response.raise_for_status()

weather = response.json()

# -------------------------
# BigQuery
# -------------------------
table_id = "weather-dashboard-503407.weather_dashboard.weather_data"

schema = [
    bigquery.SchemaField("state", "STRING"),
    bigquery.SchemaField("city", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT"),
    bigquery.SchemaField("longitude", "FLOAT"),
    bigquery.SchemaField("timezone", "STRING"),
    bigquery.SchemaField("observation_time", "TIMESTAMP"),
    bigquery.SchemaField("temperature", "FLOAT"),
    bigquery.SchemaField("humidity", "INTEGER"),
    bigquery.SchemaField("wind_speed", "FLOAT"),
    bigquery.SchemaField("inserted_at", "TIMESTAMP"),
]

# -------------------------
# Check table
# -------------------------
try:
    table = client.get_table(table_id)

    if len(table.schema) == 0:
        print("Table exists but has no schema. Updating schema...")

        table.schema = schema
        client.update_table(table, ["schema"])

        print("Schema updated.")

    else:
        print("Table schema already exists.")

except Exception:
    print("Table does not exist. Creating...")

    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table)

    print("Table created.")

# -------------------------
# Prepare row
# -------------------------
from datetime import datetime, timezone

rows = []

for location in locations:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={location['lat']}"
        f"&longitude={location['lon']}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        "&timezone=Asia/Kuala_Lumpur"
    )

    response = requests.get(url)
    response.raise_for_status()

    weather = response.json()

    rows.append({
        "state": location["state"],
        "city": location["city"],
        "latitude": weather["latitude"],
        "longitude": weather["longitude"],
        "timezone": weather["timezone"],
        "observation_time": weather["current"]["time"],
        "temperature": weather["current"]["temperature_2m"],
        "humidity": weather["current"]["relative_humidity_2m"],
        "wind_speed": weather["current"]["wind_speed_10m"],
        "inserted_at": datetime.now(timezone.utc).isoformat()
    })

errors = client.insert_rows_json(table_id, rows)

if errors:
    print(errors)
else:
    print(f"Successfully inserted {len(rows)} weather records.")