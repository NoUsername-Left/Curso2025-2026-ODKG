// App.jsx (MODIFICADO)

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Map from './components/Map';
import SearchBar from './components/SearchBar';
import FilterButtons from './components/FilterButtons';
import DistrictList from './components/DistrictList';

// --- 1. FUNCIÓN PARA CALCULAR DISTANCIA (Fórmula de Haversine) ---
// Esta función calcula la distancia en KM entre dos puntos (lat/lon)
function getDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radio de la Tierra en km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c; // Distancia en km
}
// ---------------------------------------------------------------


function App() {
  // --- ESTADOS EXISTENTES (sin cambios) ---
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('all');

  // --- 2. NUEVO ESTADO PARA MODO DE CERCANÍA ---
  // null = modo normal
  // objeto = modo cercanía
  const [proximitySearch, setProximitySearch] = useState(null);
  
  useEffect(() => {
    // ... (Tu useEffect para cargar datos no cambia) ...
    const fetchData = async () => {
      try {
        const [bikesRes, barsRes, districtsRes] = await Promise.all([
          axios.get('/api/bikingStations'),
          axios.get('/api/bars'),
          axios.get('/api/districts')
        ]);
        const bikeData = bikesRes.data.map(b => ({ ...b, type: 'bike' }));
        const barData = barsRes.data.map(b => ({ ...b, type: 'bar' }));
        setMarkers([...bikeData, ...barData]);
        setDistricts(districtsRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
  };

  const handleDistrictClick = (districtName) => {
    // Si estamos en modo cercanía, salimos de él
    if (proximitySearch) setProximitySearch(null); 
    
    if (selectedDistrict === districtName) {
      setSelectedDistrict('all');
    } else {
      setSelectedDistrict(districtName);
    }
  };
  
  // --- 3. FUNCIÓN HANDLER PARA EL BOTÓN DEL POPUP ---
  const handleProximitySearch = (originMarker) => {
    // 1. Determinar qué estamos buscando
    const targetType = originMarker.type === 'bike' ? 'bar' : 'bike';
    
    // 2. Filtrar la lista MAESTRA de marcadores para encontrar solo los candidatos
    const candidates = markers.filter(m => m.type === targetType);

    // 3. Calcular la distancia de cada candidato al origen
    const markersWithDistance = candidates.map(marker => {
      const distance = getDistance(
        originMarker.latitude, originMarker.longitude,
        marker.latitude, marker.longitude
      );
      return { marker, distance }; // Devolvemos un objeto con el marcador y su distancia
    });

    // 4. Ordenar por distancia (de más cercano a más lejano)
    markersWithDistance.sort((a, b) => a.distance - b.distance);

    // 5. Coger los 3 primeros y extraer solo el objeto 'marker'
    const top3Results = markersWithDistance.slice(0, 3).map(item => item.marker);

    // 6. ¡ACTIVAR EL MODO DE CERCANÍA!
    setProximitySearch({
      origin: originMarker,
      results: top3Results
    });
    
    // Reseteamos otros filtros para evitar confusiones
    setFilter('all');
    setSearchQuery('');
    setSelectedDistrict('all');
  };

  // --- 4. FUNCIÓN PARA RESETEAR LA VISTA ---
  const resetProximitySearch = () => {
    setProximitySearch(null);
  };


  // --- 5. LÓGICA DE FILTRADO FINAL (MODIFICADA) ---
  
  let markersForMap; // Los marcadores que realmente se enviarán al mapa

  if (proximitySearch) {
    // Si estamos en MODO CERCANÍA, ignoramos todos los filtros
    // y solo mostramos el origen y los 3 resultados.
    markersForMap = [
      proximitySearch.origin, 
      ...proximitySearch.results
    ];
  } else {
    // Si estamos en MODO NORMAL, aplicamos los filtros como siempre.
    markersForMap = markers
      .filter(marker => { // Filtro 1: Tipo (Bici/Bar/Todos)
        if (filter === 'all') return true;
        if (filter === 'bikes') return marker.type === 'bike';
        if (filter === 'bars') return marker.type === 'bar';
        return true;
      })
      .filter(marker => { // Filtro 2: Búsqueda de texto
        const query = searchQuery.toLowerCase();
        const label = (marker.label || '').toLowerCase();
        const barName = (marker.barName || '').toLowerCase();
        const addressName = (marker.addressName || '').toLowerCase();
        return label.includes(query) || 
               barName.includes(query) || 
               addressName.includes(query);
      })
      .filter(marker => { // Filtro 3: Distrito
        if (selectedDistrict === 'all') return true;
        return marker.districtName === selectedDistrict;
      });
  }


  return (
    <div className="app">
      <div className="main-content">
        <main className="map-container-wrapper">
          {loading && (
            <div className="loading-overlay">Cargando datos...</div>
          )}

          {!loading && (
            <Map 
              markers={markersForMap} // <-- 6. PASAR LA LISTA CORRECTA
              onProximitySearch={handleProximitySearch} // <-- 7. PASAR LA NUEVA FUNCIÓN
            >
              <div className="map-controls"> 
                <SearchBar
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                  handleSearch={e => e.preventDefault()}
                />
                <FilterButtons
                  filter={filter}
                  handleFilterChange={handleFilterChange}
                />
                
                {/* --- 8. BOTÓN PARA RESETEAR VISTA --- */}
                {proximitySearch && (
                  <button 
                    onClick={resetProximitySearch} 
                    className="reset-proximity-button"
                  >
                    Mostrar todos los puntos de nuevo
                  </button>
                )}
                {/* --- Fin del botón de reseteo --- */}
              </div>
            </Map>
          )}
        </main>

        <aside className="sidebar-container">
          {!loading && (
            <DistrictList
              districts={districts}
              selectedDistrict={selectedDistrict}
              onDistrictClick={handleDistrictClick}
            />
          )}
        </aside>
      </div>
    </div>
  );
}

export default App;