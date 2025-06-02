import requests
import psycopg2
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = 'YOUR_OPENWEATHER_API_KEY'
LAT, LON = -10, 48  # Paris
DB_CONFIG = {
    'dbname': 'meteo',
    'user': 'postgres',
    'password': 'nantenaina',
    'host': 'localhost',
    'port': 5432
}

def get_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

def insert_into_postgis(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO meteo_donnees (temperature, humidite, pression, geom, date)
        VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
    """, (
        data["main"]["temp"],
        data["main"]["humidity"],
        data["main"]["pressure"],
        data["coord"]["lon"],
        data["coord"]["lat"],
        datetime.now()
    ))

    conn.commit()
    conn.close()

def main():
    weather_data = get_weather_data(LAT, LON, API_KEY)
    insert_into_postgis(weather_data)
    print("✅ Données insérées avec succès.")

if __name__ == "__main__":
    main()
