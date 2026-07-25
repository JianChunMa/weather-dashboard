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
    project=PROJECT_ID
)

# -------------------------
# Malaysia State Capitals
# -------------------------

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
# Fetch Weather
# -------------------------

session = requests.Session()

rows = []

for location in locations:

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={location['lat']}"
        f"&longitude={location['lon']}"
        "&current=temperature_2m,"
        "relative_humidity_2m,"
        "wind_speed_10m"
        "&timezone=Asia/Kuala_Lumpur"
    )

    try:
        response = session.get(
            url,
            timeout=(5, 15)
        )

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

        print(f"✓ {location['city']}")

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed: {location['city']}")
        print(e)

# -------------------------
# Upload to BigQuery
# -------------------------

if not rows:
    raise Exception("No weather data collected.")

print(f"\nUploading {len(rows)} rows to BigQuery...")

errors = client.insert_rows_json(
    TABLE_ID,
    rows
)

if errors:
    print("BigQuery errors:")
    print(errors)
    raise Exception("BigQuery insert failed.")

print(f"Successfully uploaded {len(rows)} weather records.")