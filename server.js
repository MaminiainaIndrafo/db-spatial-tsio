require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const path = require('path');

const app = express();
const PORT = 3000;

const pool = new Pool({
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME
});

app.use(express.static('public'));

app.get('/api/meteo', async (req, res) => {
  const query = `
    SELECT rain,
           ST_X(geom) AS lon, ST_Y(geom) AS lat,
           date
    FROM meteo_donnees
  `;
  try {
    const { rows } = await pool.query(query);
    const features = rows.map(row => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [row.lon, row.lat] },
      properties: {
        Précipitation: row.rain,
        date: row.date
      }
    }));
    res.json({ type: "FeatureCollection", features });
  } catch (err) {
    console.error(err);
    res.status(500).send("Erreur serveur");
  }
});

app.listen(PORT, () => console.log(`🌍 Serveur sur http://localhost:${PORT}`));
