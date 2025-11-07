
const express = require('express');
const cors = require('cors');
const oxigraph = require('oxigraph');
const fs = require('fs-extra');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

let store;

async function initializeStore() {
  console.log("Inicializando base de datos en memoria...");
  store = new oxigraph.Store();
  
  const ttlPath = path.join(__dirname, '../../../rdf/transformed-data-with-links.ttl');

  const ttlData = await fs.readFile(ttlPath, 'utf-8');
  
  // <-- MIRA AQUÍ: Sintaxis de "load" corregida para eliminar el aviso
  await store.load(ttlData, 'text/turtle');
  
  console.log("Datos cargados. Servidor listo.");
}

async function sparqlQuery(query) {
  if (!store) {
    throw new Error("La base de datos en memoria no está inicializada.");
  }
  
  const results = [];
  for (const binding of store.query(query)) {
    const result = {};
    for (const [variable, term] of binding.entries()) {
      result[variable.value] = term.value;
    }
    results.push(result);
  }
  return results;
}

// --- ENDPOINTS ---

app.get('/api/bikingStations', async (req, res) => {
  const query = `
    PREFIX ns: <http://www.barnabikes.org/ODKG/handsOn/group10/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    
    SELECT ?station ?stationId ?addressName ?latitude ?longitude ?label
    WHERE {
      ?station a ns:BikingStation .
      OPTIONAL { ?station ns:stationId ?stationId }
      OPTIONAL { ?station rdfs:label ?label }
      OPTIONAL {
        ?station ns:hasAddress ?address .
        ?address ns:addressName ?addressName ;
                 ns:latitude ?latitude ;
                 ns:longitude ?longitude .
      }
    }`;
  try {
    const results = await sparqlQuery(query);
    const formatted = results.map(b => ({
      ...b,
      latitude: b.latitude ? parseFloat(b.latitude) : null,
      longitude: b.longitude ? parseFloat(b.longitude) : null,
    }));
    res.json(formatted);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: 'SPARQL query failed' });
  }
});

app.get('/api/bars', async (req, res) => {
  const query = `
    PREFIX ns: <http://www.barnabikes.org/ODKG/handsOn/group10/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    
    SELECT ?bar ?barName ?latitude ?longitude ?label
    WHERE {
      ?bar a ns:Bar .
      OPTIONAL { ?bar ns:barName ?barName }
      OPTIONAL { ?bar rdfs:label ?label }
      OPTIONAL {
        ?bar ns:hasAddress ?address .
        ?address ns:latitude ?latitude ;
                 ns:longitude ?longitude .
      }
    }`;
  try {
    const results = await sparqlQuery(query);
    const formatted = results.map(b => ({
      ...b,
      barName: b.barName || b.label,
      latitude: b.latitude ? parseFloat(b.latitude) : null,
      longitude: b.longitude ? parseFloat(b.longitude) : null,
    }));
    res.json(formatted);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: 'SPARQL query failed' });
  }
});

app.get('/api/search', async (req, res) => {
  const q = req.query.q || '';
  
  const query = `
    PREFIX ns: <http://www.barnabikes.org/ODKG/handsOn/group10/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    
    SELECT ?s ?type ?name ?latitude ?longitude
    WHERE {
      { ?s a ns:Bar ; rdfs:label ?label . BIND("Bar" as ?type) . OPTIONAL { ?s ns:barName ?name } }
      UNION
      { ?s a ns:BikingStation ; rdfs:label ?label . BIND("BikingStation" as ?type) . OPTIONAL { ?s ns:stationId ?name } }
      OPTIONAL { ?s ns:hasAddress ?addr . ?addr ns:latitude ?latitude ; ns:longitude ?longitude }
      FILTER (regex(str(?label), "${q}", "i") || regex(str(?name), "${q}", "i"))
    }`;
  try {
    const results = await sparqlQuery(query);
    const formatted = results.map(b => ({
      uri: b.s,
      type: b.type,
      name: b.name || b.label,
      latitude: b.latitude ? parseFloat(b.latitude) : null,
      longitude: b.longitude ? parseFloat(b.longitude) : null,
    }));
    res.json(formatted);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: 'SPARQL query failed' });
  }
});

const PORT = process.env.PORT || 4000;

initializeStore()
  .then(() => {
    app.listen(PORT, () => console.log(`Server listening on ${PORT}`));
  })
  .catch(error => {
    console.error("Error al inicializar la base de datos:", error);
    process.exit(1);
  });