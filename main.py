from fastapi import FastAPI, HTTPException
import requests
import psycopg2
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["http://localhost:3000"] pour être plus sécurisé
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- CONFIGURATION BASE --- 
DB_CONFIG = {
    'dbname': 'tsiory_these',
    'user': 'postgres',
    'password': '3421andri',
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


def insert_into_postgis(data, lon, lat,gid,date):
    """ Insère les données météo dans la base de données PostGIS """
    rain_1h = data.get("rain", {}).get("1h", 0.0)  # Prendre la pluie sur 1h (0 si non disponible)
    id_type=1
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                print(f"Insertion des données pour lat: {lat}, lon: {lon}, pluie: {rain_1h}")
                cur.execute("""
                    INSERT INTO risque2 (val_degre_risque, id_type,gid, did)
                    VALUES (%s,%s, %s, %s)
                """, (
                    rain_1h,
                    id_type,
                    gid,
                    date
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
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for coord in coordinates:
            gid, lon, lat = coord
            # Récupérer les données météo pour chaque point
            weather_data = get_weather_data(lat, lon, API_KEY)
            # Insérer les données dans la base de données
            insert_into_postgis(weather_data, lon, lat,gid,date)
        
        return {"message": "✅ Données insérées avec succès pour tous les points.",
                "cordonnées":coordinates}
    
    except HTTPException as e:
        raise e  # Propager l'exception HTTP
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/districts")
def get_districts():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        id, 
                        ST_AsGeoJSON(geom)::json AS geometry,
                        objectid, 
                        district, 
                        p_code, 
                        d_code, 
                        region, 
                        reg_pcode, 
                        r_code, 
                        source
                    FROM public.district
                """)
                rows = cur.fetchall()

                features = [{
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": id,
                        "objectid": objectid,
                        "district": district,
                        "p_code": p_code,
                        "d_code": d_code,
                        "region": region,
                        "reg_pcode": reg_pcode,
                        "r_code": r_code,
                        "source": source
                    }
                } for id, geometry, objectid, district, p_code, d_code, region, reg_pcode, r_code, source in rows]

                return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/communes")
def get_communes():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ogc_fid, 
                        ST_AsGeoJSON(geom)::json AS geometry,
                        com_pcode, 
                        c_code, 
                        commune_na, 
                        bngrc_com_, 
                        dist_pcode, 
                        district_n, 
                        bngrc_d_co, 
                        bngrc_dis_, 
                        dis_fkt, 
                        reg_pcode, 
                        region_nam, 
                        bngrc_r_co, 
                        bngrc_reg_, 
                        reg_fkt_sh, 
                        prov_code, 
                        old_provin, 
                        notes, 
                        old_distri, 
                        source, 
                        shape_leng, 
                        shape_area
                    FROM public.commune
                """)
                rows = cur.fetchall()

                features = [{
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "ogc_fid": ogc_fid,
                        "com_pcode": com_pcode,
                        "c_code": c_code,
                        "commune_na": commune_na,
                        "bngrc_com_": bngrc_com_,
                        "dist_pcode": dist_pcode,
                        "district_n": district_n,
                        "bngrc_d_co": bngrc_d_co,
                        "bngrc_dis_": bngrc_dis_,
                        "dis_fkt": dis_fkt,
                        "reg_pcode": reg_pcode,
                        "region_nam": region_nam,
                        "bngrc_r_co": bngrc_r_co,
                        "bngrc_reg_": bngrc_reg_,
                        "reg_fkt_sh": reg_fkt_sh,
                        "prov_code": prov_code,
                        "old_provin": old_provin,
                        "notes": notes,
                        "old_distri": old_distri,
                        "source": source,
                        "shape_leng": shape_leng,
                        "shape_area": shape_area
                    }
                } for ogc_fid, geometry, com_pcode, c_code, commune_na, bngrc_com_, dist_pcode, district_n, bngrc_d_co, bngrc_dis_, dis_fkt, reg_pcode, region_nam, bngrc_r_co, bngrc_reg_, reg_fkt_sh, prov_code, old_provin, notes, old_distri, source, shape_leng, shape_area in rows]

                return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/regions")
def get_region():
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            ogc_fid, 
                            ST_AsGeoJSON(geom)::json AS geometry,
                            reg_pcode, 
                            r_code, 
                            region_nam, 
                            bngrc_r_co, 
                            bngrc_reg_, 
                            reg_fkt_sh, 
                            prov_code, 
                            old_provin, 
                            source, 
                            notes, 
                            shape_leng, 
                            shape_area, 
                            surface, 
                            surface_ha
                        FROM public.region
                    """)
                    rows = cur.fetchall()

                    features = [{
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {
                            "ogc_fid": ogc_fid,
                            "reg_pcode": reg_pcode,
                            "r_code": r_code,
                            "region_nam": region_nam,
                            "bngrc_r_co": bngrc_r_co,
                            "bngrc_reg_": bngrc_reg_,
                            "reg_fkt_sh": reg_fkt_sh,
                            "prov_code": prov_code,
                            "old_provin": old_provin,
                            "source": source,
                            "notes": notes,
                            "shape_leng": shape_leng,
                            "shape_area": shape_area,
                            "surface": surface,
                            "surface_ha": surface_ha
                        }
                    } for ogc_fid, geometry, reg_pcode, r_code, region_nam, bngrc_r_co, bngrc_reg_, reg_fkt_sh, prov_code, old_provin, source, notes, shape_leng, shape_area, surface, surface_ha in rows]

                    return {"type": "FeatureCollection", "features": features}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données : {str(e)}")


@app.get("/api/fokotany")
def get_fokotany():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ogc_fid, 
                        ST_AsGeoJSON(geom)::json AS geometry,
                        p_code, 
                        fokontany_, 
                        fkt_bngrc_, 
                        c_fkt_bngr, 
                        com_pcode, 
                        c_code_bng, 
                        commune_na, 
                        bngrc_com_, 
                        dist_pcode, 
                        district_n, 
                        bngrc_d_co, 
                        bngrc_dis_, 
                        dis_fkt, 
                        reg_pcode, 
                        region_nam, 
                        bngrc_r_co, 
                        bngrc_reg_, 
                        reg_fkt_sh, 
                        prov_code, 
                        old_provin, 
                        milieu, 
                        old_distri, 
                        source, 
                        shape_leng, 
                        shape_area
                    FROM public.fokotany;
                """)
                rows = cur.fetchall()

                features = [{
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "ogc_fid": ogc_fid,
                        "p_code": p_code,
                        "fokontany_": fokontany_,
                        "fkt_bngrc_": fkt_bngrc_,
                        "c_fkt_bngr": c_fkt_bngr,
                        "com_pcode": com_pcode,
                        "c_code_bng": c_code_bng,
                        "commune_na": commune_na,
                        "bngrc_com_": bngrc_com_,
                        "dist_pcode": dist_pcode,
                        "district_n": district_n,
                        "bngrc_d_co": bngrc_d_co,
                        "bngrc_dis_": bngrc_dis_,
                        "dis_fkt": dis_fkt,
                        "reg_pcode": reg_pcode,
                        "region_nam": region_nam,
                        "bngrc_r_co": bngrc_r_co,
                        "bngrc_reg_": bngrc_reg_,
                        "reg_fkt_sh": reg_fkt_sh,
                        "prov_code": prov_code,
                        "old_provin": old_provin,
                        "milieu": milieu,
                        "old_distri": old_distri,
                        "source": source,
                        "shape_leng": shape_leng,
                        "shape_area": shape_area
                    }
                } for ogc_fid, geometry, p_code, fokontany_, fkt_bngrc_, c_fkt_bngr, com_pcode, c_code_bng, commune_na, bngrc_com_, dist_pcode, district_n, bngrc_d_co, bngrc_dis_, dis_fkt, reg_pcode, region_nam, bngrc_r_co, bngrc_reg_, reg_fkt_sh, prov_code, old_provin, milieu, old_distri, source, shape_leng, shape_area in rows]

                return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
