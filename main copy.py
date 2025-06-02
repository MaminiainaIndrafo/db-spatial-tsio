from fastapi import FastAPI, Query
import requests
import psycopg2
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()

# --- CONFIGURATION BASE ---
DB_CONFIG = {
    'dbname': 'DWSTR',
    'user': 'postgres',
    'password': 'nantenaina',
    'host': 'localhost',
    'port': 5432
}

API_KEY = '6bc1fc195f8503644a431c983761df69'  # Remplace avec ta vraie clé


def get_weather_data(lat: float, lon: float, api_key: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()


def insert_into_postgis(data):
    rain_1h= data.get("rain", {}).get("1h", 0.0)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO meteo_donnees (rain, geom, date)
        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
    """, (
        rain_1h,
        data["coord"]["lon"],
        data["coord"]["lat"],
        datetime.now()
    ))
    
    conn.commit()
    cur.close()
    conn.close()


    
@app.get("/meteo")
def collect_meteo(lat: float = Query(...), lon: float = Query(...)):
    try:
        weather_data = get_weather_data(lat, lon, API_KEY)
        insert_into_postgis(weather_data)
        return {
            "message": "✅ Données insérées avec succès",
            "coord": weather_data["coord"],
            "rain": weather_data["main"]["rain"],
            

        }
    except Exception as e:
        return {"error": str(e)}
