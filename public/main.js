const map = L.map('map').setView([-20, 50], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let districtLayer = null;
let meteoLayer = null;
let districtLayerRegrouper = null;
let communeLayer = null;
let fokotanyLayer = null;
let regionLayer = null;

function getColorByPrecipitation(moyenne) {
    return moyenne > 1 ? '#800026' :
        moyenne > 0.75 ? '#BD0026' :
            moyenne > 0.5 ? '#E31A1C' :
                moyenne > 0.25 ? '#FC4E2A' :
                    moyenne > 0.1 ? '#FD8D3C' :
                        moyenne > 0 ? '#FED976' :
                            '#FFEDA0'; // 0 ou aucune donnée
}


function loadMeteoData(dateFilter = null) {
    if (meteoLayer) {
        map.removeLayer(meteoLayer);
    }

    fetch('/api/meteo')
        .then(res => res.json())
        .then(data => {
            // Si un filtre de date est donné, on filtre les features
            if (dateFilter) {
                data.features = data.features.filter(f => f.properties.date.startsWith(dateFilter));
            }

            meteoLayer = L.geoJSON(data, {
                pointToLayer: function (feature, latlng) {
                    const rain = feature.properties.Précipitation || 0;

                    // Définir un rayon de cercle basé sur la pluie (entre 0 et 5)
                    const radius = 5 + (rain * 10);  // par exemple : pluie 0 -> 5px, pluie 5 -> 30px

                    return L.circleMarker(latlng, {
                        radius: radius,
                        fillColor: getColor(rain),
                        color: "#000",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                },
                onEachFeature: function (feature, layer) {
                    const p = feature.properties;
                    layer.bindPopup(`
                        <strong>Précipitation :</strong> ${p.Précipitation} mm<br/>
                        <strong>Date :</strong> ${new Date(p.date).toLocaleString()}
                    `);
                }
            }).addTo(map);
        })
        .catch(error => {
            console.error('Erreur lors du chargement des données météo :', error);
        });
}

function loadRegionLayer() {
    fetch('http://localhost:8000/api/regions')
        .then(response => response.json())
        .then(regionData => {
            // Charger les points météo pour traitement
            fetch('/api/meteo')
                .then(res => res.json())
                .then(meteoData => {
                    regionLayer = L.geoJSON(regionData, {
                        style: {
                            color: 'bleu',
                            weight: 2,
                            fillOpacity: 0.1
                        },
                        onEachFeature: (feature, layer) => {
                            const regionPolygon = feature;
                            const p = feature.properties;

                            // Filtrer les points météo à l’intérieur de la région
                            const pointsInside = meteoData.features.filter(pt =>
                                turf.booleanPointInPolygon(pt, regionPolygon)
                            );

                            // Calculer la moyenne des précipitations
                            const total = pointsInside.reduce((sum, pt) => sum + (pt.properties.Précipitation || 0), 0);
                             const moyenne = pointsInside.length > 0 ? total / pointsInside.length : 0;
 
                             // Ajouter la moyenne dans les propriétés
                             p.moyenne_precipitation = moyenne.toFixed(2);

                            //const moyenne = layer.feature.properties.moyenne_precipitation || 0;
                            const color = getColorByPrecipitation(moyenne);

                            layer.setStyle({
                                fillColor: color,
                                fillOpacity: 0.7,
                                color: 'black',
                                weight: 1
                            });

                            // Popup enrichi
                            layer.bindPopup(`
                        <strong>Région:</strong> ${p.region_nam}<br/>
                        <strong>Code:</strong> ${p.reg_pcode}<br/>
                        <strong>💧 Moyenne Précipitation:</strong> ${moyenne.toFixed(2)} mm
                    `);

                            // Zoom au clic
                            layer.on('click', function () {
                                map.fitBounds(layer.getBounds());
                                layer.openPopup();
                            });
                        }
                    }).addTo(map);
                })
        })
}

function loadDistrictLayer() {
    fetch('http://localhost:8000/api/districts')
        .then(response => response.json())
        .then(districtData => {
            // Charger les points météo pour traitement
            fetch('/api/meteo')
                .then(res => res.json())
                .then(meteoData => {

                    districtLayer = L.geoJSON(districtData, {
                        style: {
                            color: 'blue',
                            weight: 2,
                            fillOpacity: 0.1
                        },
                        onEachFeature: (feature, layer) => {
                            const districtPolygon = feature;
                            const p = feature.properties;

                            // Filtrer les points météo à l’intérieur du district
                            const pointsInside = meteoData.features.filter(pt =>
                                turf.booleanPointInPolygon(pt, districtPolygon)
                            );

                            // Calculer la moyenne des précipitations
                            const total = pointsInside.reduce((sum, pt) => sum + (pt.properties.Précipitation || 0), 0);
                            const moyenne = pointsInside.length > 0 ? total / pointsInside.length : 0;
 
                             // Ajouter la moyenne dans les propriétés
                             
                            p.moyenne_precipitation = moyenne.toFixed(2);

                            //const moyenne = layer.feature.properties.moyenne_precipitation || 0;
                            const color = getColorByPrecipitation(moyenne);

                            layer.setStyle({
                                fillColor: color,
                                fillOpacity: 0.7,
                                color: 'black',
                                weight: 1
                            });

                            // Popup enrichi
                            layer.bindPopup(`
                                <strong>District:</strong> ${p.district}<br/>
                                <strong>Région:</strong> ${p.region}<br/>
                                <strong>Code:</strong> ${p.d_code}<br/>
                                <strong>💧 Moyenne Précipitation:</strong> ${moyenne.toFixed(2)} mm
                            `);

                            // Zoom au clic
                            layer.on('click', function () {
                                map.fitBounds(layer.getBounds());
                                layer.openPopup();
                            });
                        }
                    }).addTo(map);

                    districtLayerRegrouper = districtLayer;

                });
        });
}

function loadCommuneLayer() {
    fetch('http://localhost:8000/api/communes')
        .then(response => response.json())
        .then(communeData => {
            fetch('/api/meteo')
                .then(res => res.json())
                .then(meteoData => {
                    communeLayer = L.geoJSON(communeData, {
                        style: {
                            color: 'bleu',
                            weight: 2,
                            fillOpacity: 0.1
                        },
                        onEachFeature: (feature, layer) => {
                            const communePolygon = feature;
                            const p = feature.properties;

                            const pointsInside = meteoData.features.filter(pt =>
                                turf.booleanPointInPolygon(pt, communePolygon)
                            );

                            const total = pointsInside.reduce((sum, pt) => sum + (pt.properties.Précipitation || 0), 0);
                            const moyenne = pointsInside.length > 0 ? total / pointsInside.length : 0;

                            p.moyenne_precipitation = moyenne.toFixed(2);

                            //const moyenne = layer.feature.properties.moyenne_precipitation || 0;
                            const color = getColorByPrecipitation(moyenne);

                            layer.setStyle({
                                fillColor: color,
                                fillOpacity: 0.7,
                                color: 'black',
                                weight: 1
                            });

                            layer.bindPopup(`
                                <strong>Commune:</strong> ${p.commune_na}<br/>
                                <strong>Région:</strong> ${p.region_nam}<br/>
                                <strong>Code:</strong> ${p.c_code}<br/>
                                <strong>💧 Moyenne Précipitation:</strong> ${moyenne.toFixed(2)} mm
                            `);

                            layer.on('click', function () {
                                map.fitBounds(layer.getBounds());
                                layer.openPopup();
                            });
                        }
                    }).addTo(map);
                });
        });
}


function loadFokotanyLayer() {
    fetch('http://localhost:8000/api/fokotany')
        .then(response => response.json())
        .then(fokotanyData => {
            // Charger les points météo pour traitement
            fetch('/api/meteo')
                .then(res => res.json())
                .then(meteoData => {

                    fokotanyLayer = L.geoJSON(fokotanyData, {
                        style: {
                            color: 'bleu',
                            weight: 2,
                            fillOpacity: 0.1
                        },
                        onEachFeature: (feature, layer) => {
                            const fokotanyPolygon = feature;
                            const p = feature.properties;

                            // Filtrer les points météo à l’intérieur de la fokotany
                            const pointsInside = meteoData.features.filter(pt =>
                                turf.booleanPointInPolygon(pt, fokotanyPolygon)
                            );

                            // Calculer la moyenne des précipitations
                            const total = pointsInside.reduce((sum, pt) => sum + (pt.properties.Précipitation || 0), 0);
                            const moyenne = pointsInside.length > 0 ? total / pointsInside.length : 0;

                            // Ajouter la moyenne dans les propriétés
                            p.moyenne_precipitation = moyenne.toFixed(2);

                            //const moyenne = layer.feature.properties.moyenne_precipitation || 0;
                            const color = getColorByPrecipitation(moyenne);

                            layer.setStyle({
                                fillColor: color,
                                fillOpacity: 0.7,
                                color: 'black',
                                weight: 1
                            });
                            // Popup enrichi
                            layer.bindPopup(`
                        <strong>Fokotany:</strong> ${p.fokontany_}<br/>
                        <strong>Commune:</strong> ${p.commune_na}<br/>
                        <strong>Région:</strong> ${p.region_nam}<br/>
                        <strong>Code:</strong> ${p.f_code}<br/>
                        <strong>💧 Moyenne Précipitation:</strong> ${moyenne.toFixed(2)} mm
                    `);

                            // Zoom au clic
                            layer.on('click', function () {
                                map.fitBounds(layer.getBounds());
                                layer.openPopup();
                            });
                        }
                    }).addTo(map);
                });
        });
}

loadRegionLayer();
loadDistrictLayer();
loadCommuneLayer();
loadFokotanyLayer();

document.getElementById('btn-regrouper').addEventListener('click', function () {
    if (!districtLayerRegrouper) return;

    districtLayerRegrouper.eachLayer(layer => {
        const moyenne = layer.feature.properties.moyenne_precipitation || 0;
        const color = getColorByPrecipitation(moyenne);

        layer.setStyle({
            fillColor: color,
            fillOpacity: 0.7,
            color: 'black',
            weight: 1
        });

        // On peut aussi mettre à jour le popup si besoin
        layer.bindPopup(`
            <strong>District:</strong> ${layer.feature.properties.district}<br/>
            <strong>Moyenne Précipitation:</strong> ${moyenne} mm
        `);
    });
});


// Une fonction simple pour changer la couleur en fonction de la pluie
function getColor(rain) {
    return rain > 4 ? '#08306b' :
        rain > 3 ? '#2171b5' :
            rain > 2 ? '#4292c6' :
                rain > 1 ? '#6baed6' :
                    rain > 0 ? '#9ecae1' :
                        '#c6dbef';
}

// Exemple appel sans filtre au début
loadMeteoData();

const loadButton = document.getElementById('loadButton');
const buttonText = document.getElementById('buttonText');
const loaderIcon = document.getElementById('loader');
const messageDiv = document.getElementById('message');

loadButton.addEventListener('click', () => {
    // Désactiver bouton + afficher loader
    loadButton.disabled = true;
    loaderIcon.classList.remove('hidden');
    buttonText.textContent = "Chargement...";

    fetch('http://127.0.0.1:8000/collect_all_meteo')
        .then(response => response.json())
        .then(data => {
            console.log('Réponse serveur:', data);
            if (data.error) {
                messageDiv.innerHTML = `<div class="text-red-600 font-semibold">❌ ${data.error}</div>`;
            } else {
                messageDiv.innerHTML = `<div class="text-green-600 font-semibold">✅ Données collectées avec succès !</div>`;
                loadMeteoData();
            }
        })
        .catch(error => {
            console.error('Erreur serveur:', error);
            messageDiv.innerHTML = `<div class="text-red-600 font-semibold">❌ Erreur lors de la collecte des données.</div>`;
        })
        .finally(() => {
            // Réactiver bouton + cacher loader
            loadButton.disabled = false;
            loaderIcon.classList.add('hidden');
            buttonText.textContent = "Load data";
        });
});


const filterButton = document.getElementById('filterButton');
const dateFilterInput = document.getElementById('dateFilter');

filterButton.addEventListener('click', () => {
    const dateFilter = dateFilterInput.value;
    loadMeteoData(dateFilter);
});

document.getElementById("toggleRegion").addEventListener("click", () => {
    if (regionLayer) {
        if (map.hasLayer(regionLayer)) {
            map.removeLayer(regionLayer);
            document.getElementById("toggleRegion").textContent = "🗺️ Region : masqué";
        } else {
            map.addLayer(regionLayer);
            document.getElementById("toggleRegion").textContent = "🗺️ Region : visible";
        }
    }
});

document.getElementById("toggleMeteo").addEventListener("click", () => {
    if (meteoLayer) {
        if (map.hasLayer(meteoLayer)) {
            map.removeLayer(meteoLayer);
            document.getElementById("toggleMeteo").textContent = "🌧️ Météo : masqué";
        } else {
            map.addLayer(meteoLayer);
            document.getElementById("toggleMeteo").textContent = "🌧️ Météo : visible";
        }
    }
});


document.getElementById("toggleDistricts").addEventListener("click", () => {
    if (districtLayer) {
        if (map.hasLayer(districtLayer)) {
            map.removeLayer(districtLayer);
            document.getElementById("toggleDistricts").textContent = "🗺️ Districts : masqué";
        } else {
            map.addLayer(districtLayer);
            document.getElementById("toggleDistricts").textContent = "🗺️ Districts : visible";
        }
    }
});

document.getElementById("btn-regrouper").addEventListener("click", () => {
    if (districtLayerRegrouper) {
        if (map.hasLayer(districtLayerRegrouper)) {
            map.removeLayer(districtLayerRegrouper);
            document.getElementById("btn-regrouper").textContent = "Regrouper (Colorier) : masqué";
        } else {
            map.addLayer(districtLayerRegrouper);
            document.getElementById("btn-regrouper").textContent = "Regrouper (Colorier) : visible";
        }
    }
});

document.getElementById("toggleCommunes").addEventListener("click", () => {
    if (communeLayer) {
        if (map.hasLayer(communeLayer)) {
            map.removeLayer(communeLayer);
            document.getElementById("toggleCommunes").textContent = "🏞️ Communes : masqué";
        } else {
            map.addLayer(communeLayer);
            document.getElementById("toggleCommunes").textContent = "🏞️ Communes : visible";
        }
    }
});

document.getElementById("toggleFokotany").addEventListener("click", () => {
    if (fokotanyLayer) {
        if (map.hasLayer(fokotanyLayer)) {
            map.removeLayer(fokotanyLayer);
            document.getElementById("toggleFokotany").textContent = "🏞️ Fokotany : masqué";
        } else {
            map.addLayer(fokotanyLayer);
            document.getElementById("toggleFokotany").textContent = "🏞️ Fokotany : visible";
        }
    }
});
