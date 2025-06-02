from fastapi import FastAPI, Query, HTTPException
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
    """ Récupère les données météo de l'API OpenWeather """
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des données météo.")
    return response.json()


def insert_into_postgis(data, lon, lat):
    """ Insère les données météo dans la base de données PostGIS """
    rain_1h = data.get("rain", {}).get("1h", 0.0)  # Prendre la pluie sur 1h (0 si non disponible)
    
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                print(f"Insertion des données pour lat: {lat}, lon: {lon}, pluie: {rain_1h}")
                cur.execute("""
                    INSERT INTO meteo_donnees (rain, geom, date)
                    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
                """, (
                    rain_1h,
                    lon,
                    lat,
                    datetime.now()
                ))
                conn.commit()  # Bien que le commit soit fait automatiquement dans le bloc `with`
                print("Données insérées avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'insertion dans la base de données : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion dans la base de données : {str(e)}")


def get_coordinates_from_db():
    """ Récupère les coordonnées (longitude, latitude) des points dans la base de données """
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT gid, ST_X(geom) as lon, ST_Y(geom) as lat
                    FROM point_location
                    WHERE gid BETWEEN 1 AND 205
                """)
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des coordonnées : {str(e)}")


@app.get("/collect_all_meteo")
def collect_all_meteo():
    """ Endpoint pour collecter et insérer les données météo pour tous les points """
    try:
        # Récupérer les coordonnées de la base de données
        coordinates = get_coordinates_from_db()
        
        for coord in coordinates:
            point_id, lon, lat = coord
            # Récupérer les données météo pour chaque point
            weather_data = get_weather_data(lat, lon, API_KEY)
            # Insérer les données dans la base de données
            insert_into_postgis(weather_data, lon, lat)
        
        return {"message": "✅ Données insérées avec succès pour tous les points.",
                "cordonnées":coordinates}
    
    except HTTPException as e:
        raise e  # Propager l'exception HTTP
    except Exception as e:
        return {"error": str(e)}
