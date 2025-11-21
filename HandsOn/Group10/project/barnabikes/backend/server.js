// server.js (MODIFICADO)

const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const GRAPHDB_ENDPOINT = process.env.GRAPHDB_ENDPOINT || 'http://sergio-IdeaPad-Slim-5-16IMH9:7200/repositories/OpenData';

function sparqlQuery(query) {
  return axios.get(GRAPHDB_ENDPOINT, {
    params: { query },
    headers: { 'Accept': 'application/sparql-results+json' }
  }).then(r => r.data);
}


app.get('/api/bikingStations', async (req, res) => {
  // 1. MODIFICAMOS LA CONSULTA para pedir ?addressType y ?addressNumber
  const query = `PREFIX ns: <http://www.barnabikes.org/ODKG/handsOn/group10/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?station ?stationId ?latitude ?longitude ?districtName
       ?addressType ?addressName ?addressNumber
WHERE {
  ?station a ns:BikingStation .
  OPTIONAL { ?station ns:stationId ?stationId }
  OPTIONAL {
    ?station ns:hasAddress ?address .
    ?address ns:latitude ?latitude ;
             ns:longitude ?longitude .
    
    # --- Pedimos los componentes de la dirección ---
    OPTIONAL { ?address ns:addressType ?addressType }
    OPTIONAL { ?address ns:addressName ?addressName }
    OPTIONAL { ?address ns:addressNumber ?addressNumber }
    
    # --- Pedimos el distrito ---
    OPTIONAL {
      ?address ns:hasNeighborhood ?neighborhood .
      ?neighborhood ns:hasDistrict ?district .
      ?district ns:districtName ?districtName .
    }
  }
}`;
  try {
    const data = await sparqlQuery(query);
    console.log(`[Backend] Datos de GraphDB (Bikes): ${data.results.bindings.length} resultados.`);
    
    // 2. MODIFICAMOS EL MAPA para crear los nuevos campos
    const results = data.results.bindings.map(b => {
      // Construimos la dirección completa (ej: "CARRER DEL GUINARDÓ, 123")
      const fullAddress = [
        b.addressType?.value, 
        b.addressName?.value, 
        b.addressNumber?.value
      ].filter(Boolean).join(' '); // Filtra nulos y une con espacios

      return {
        type: 'bike',
        uri: b.station?.value,
        stationId: b.stationId?.value,
        latitude: b.latitude ? parseFloat(b.latitude.value) : null,
        longitude: b.longitude ? parseFloat(b.longitude.value) : null,
        districtName: b.districtName?.value,
        
        // --- Campos nuevos para el popup ---
        displayName: fullAddress || 'Estación de Bici', // El Título
        displayAddress: b.districtName?.value || 'Sin distrito' // El Subtítulo (dirección)
      }
    });
    
    res.json(results);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: 'SPARQL query failed' });
  }
});


app.get('/api/bars', async (req, res) => {
  // 1. MODIFICAMOS LA CONSULTA para pedir ?addressType y ?addressNumber
  const query = `PREFIX ns: <http://www.barnabikes.org/ODKG/handsOn/group10/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?bar ?barName ?latitude ?longitude ?districtName ?tipo
       ?addressType ?addressName ?addressNumber
WHERE {
  ?bar a ns:Bar .
  OPTIONAL { ?bar ns:barName ?barName }
  OPTIONAL {
    ?bar ns:hasAddress ?address .
    ?address ns:latitude ?latitude ;
             ns:longitude ?longitude .
    ?bar ns:barType ?tipo

    # --- Pedimos los componentes de la dirección ---
    OPTIONAL { ?address ns:addressType ?addressType }
    OPTIONAL { ?address ns:addressName ?addressName }
    OPTIONAL { ?address ns:addressNumber ?addressNumber }

    # --- Pedimos el distrito ---
    OPTIONAL {
      ?address ns:hasNeighborhood ?neighborhood .
      ?neighborhood ns:hasDistrict ?district .
      ?district ns:districtName ?districtName .
    }
  }
}`;
  try {
    const data = await sparqlQuery(query);
    console.log(`[Backend] Datos de GraphDB (Bars): ${data.results.bindings.length} resultados.`);

    // 2. MODIFICAMOS EL MAPA para crear los nuevos campos
    const results = data.results.bindings.map(b => {
      // Construimos la dirección completa (ej: "CARRER DEL GUINARDÓ, 123")
      const fullAddress = [
        b.addressType?.value, 
        b.addressName?.value, 
        b.addressNumber?.value
      ].filter(Boolean).join(' '); // Filtra nulos y une con espacios

      return {
        type: 'bar',
        uri: b.bar?.value,
        barName: b.barName?.value, // Mantenemos este por si acaso
        latitude: b.latitude ? parseFloat(b.latitude.value) : null,
        longitude: b.longitude ? parseFloat(b.longitude.value) : null,
        districtName: b.districtName?.value,
        

        // --- Campos nuevos para el popup ---
        displayName: b.barName?.value || 'Bar sin nombre', // El Título
        displayAddress: fullAddress || 'Sin dirección', // El Subtítulo (dirección)
        barType: b.tipo?.value
      }
    });

    res.json(results);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: 'SPARQL query failed' });
  }
});


// ... (tu endpoint /api/districts no necesita cambios) ...
app.get('/api/districts', async (req, res) => {
  const query = `
    PREFIX ns: <http://www.barnabikes.org/ODKG/handsOn/group10/>
    SELECT DISTINCT ?districtName
    WHERE {
      ?district a ns:District .
      ?district ns:districtName ?districtName .
    }
    ORDER BY ?districtName
  `;
  try {
    const data = await sparqlQuery(query);
    const results = data.results.bindings.map(b => b.districtName.value);
    res.json(results);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: 'SPARQL query failed for districts' });
  }
});


const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Server listening on ${PORT}`));