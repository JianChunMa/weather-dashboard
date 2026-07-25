import json
import os
from datetime import datetime, timezone

import requests
from google.cloud import bigquery
from google.oauth2 import service_account

# -------------------------
# Configuration
# -------------------------

PROJECT_ID = "weather-dashboard-503407"
TABLE_ID = f"{PROJECT_ID}.weather_dashboard.weather_data"

# -------------------------
# Authentication
# -------------------------

credentials = service_account.Credentials.from_service_account_file("key.json")
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

# -------------------------
# Malaysia State Capitals
# -------------------------
# -------------------------
# Malaysia State Capitals & Federal Territories
# -------------------------

locations = [
    {"state": "Johor", "city": "Johor Bahru", "lat": 1.4927, "lon": 103.7414, "region": "peninsula"},
    {"state": "Kedah", "city": "Alor Setar", "lat": 6.1248, "lon": 100.3678, "region": "peninsula"},
    {"state": "Kelantan", "city": "Kota Bharu", "lat": 6.1254, "lon": 102.2386, "region": "peninsula"},
    {"state": "Melaka", "city": "Melaka City", "lat": 2.1896, "lon": 102.2501, "region": "peninsula"},
    {"state": "Negeri Sembilan", "city": "Seremban", "lat": 2.7297, "lon": 101.9381, "region": "peninsula"},
    {"state": "Pahang", "city": "Kuantan", "lat": 3.8077, "lon": 103.3260, "region": "peninsula"},
    {"state": "Perak", "city": "Ipoh", "lat": 4.5975, "lon": 101.0901, "region": "peninsula"},
    {"state": "Perlis", "city": "Kangar", "lat": 6.4414, "lon": 100.1986, "region": "peninsula"},
    {"state": "Penang", "city": "George Town", "lat": 5.4141, "lon": 100.3288, "region": "peninsula"},
    {"state": "Sabah", "city": "Kota Kinabalu", "lat": 5.9804, "lon": 116.0735, "region": "borneo"},
    {"state": "Sarawak", "city": "Kuching", "lat": 1.5533, "lon": 110.3592, "region": "borneo"},
    {"state": "Selangor", "city": "Shah Alam", "lat": 3.0738, "lon": 101.5183, "region": "peninsula"},
    {"state": "Terengganu", "city": "Kuala Terengganu", "lat": 5.3302, "lon": 103.1408, "region": "peninsula"},
    {"state": "Kuala Lumpur", "city": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869, "region": "peninsula"},
    {"state": "Putrajaya", "city": "Putrajaya", "lat": 2.9264, "lon": 101.6964, "region": "peninsula"},
    {"state": "Labuan", "city": "Victoria", "lat": 5.2831, "lon": 115.2308, "region": "borneo"},
]

# -------------------------
# 1. Fetch & Stream to BigQuery
# -------------------------

session = requests.Session()
rows = []

for location in locations:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={location['lat']}"
        f"&longitude={location['lon']}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        "&timezone=Asia/Kuala_Lumpur"
    )

    try:
        response = session.get(url, timeout=(5, 15))
        response.raise_for_status()
        weather = response.json()

        rows.append({
            "region": location["region"],
            "state": location["state"],
            "city": location["city"],
            "latitude": weather["latitude"],
            "longitude": weather["longitude"],
            "timezone": weather["timezone"],
            "observation_time": weather["current"]["time"],
            "temperature": weather["current"]["temperature_2m"],
            "humidity": weather["current"]["relative_humidity_2m"],
            "wind_speed": weather["current"]["wind_speed_10m"],
            "weather_code": weather["current"].get("weather_code", 0),
            "inserted_at": datetime.now(timezone.utc).isoformat()
        })
        print(f"✓ {location['city']}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed: {location['city']}\n{e}")

if rows:
    errors = client.insert_rows_json(TABLE_ID, rows)
    if errors:
        raise Exception(f"BigQuery insert failed: {errors}")
    print(f"Uploaded {len(rows)} records to BigQuery.")

# -------------------------
# 2. Query BigQuery & Export data.json
# -------------------------

# Query latest reading per city
latest_query = f"""
    SELECT city, state, temperature, humidity, wind_speed, weather_code, observation_time
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY city ORDER BY observation_time DESC) as rn
        FROM `{TABLE_ID}`
    )
    WHERE rn = 1
"""
latest_rows = [dict(row) for row in client.query(latest_query).result()]

# Query 24-hour history for trends
trend_query = f"""
    SELECT city, temperature, observation_time
    FROM `{TABLE_ID}`
    WHERE CAST(observation_time AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY city, observation_time ASC
"""
trend_rows = [dict(row) for row in client.query(trend_query).result()]

# Package and output data.json
export_data = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "current": latest_rows,
    "trends": trend_rows
}

with open("data.json", "w") as f:
    json.dump(export_data, f, indent=2, default=str)

print("Generated data.json from BigQuery.")