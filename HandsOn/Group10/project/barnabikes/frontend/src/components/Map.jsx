// src/components/Map.jsx (MODIFICADO)

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import MarkerPopup from './MarkerPopup'; // <-- 1. IMPORTAR EL NUEVO COMPONENTE

// --- Iconos personalizados (bikeIcon y barIcon) ---
// (Tu código de iconos va aquí, no lo borres)
const bikeIcon = new L.Icon({
  // 👇 Esto le dice al navegador que busque "bike.jpg" en la misma carpeta
  iconUrl: './../../public/bike.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  
  // --- IMPORTANTE ---
  // He ajustado los tamaños para que se parezcan a tu imagen
  iconSize: [35, 35],   // [ancho, alto] (ajusta esto al tamaño real)
  iconAnchor: [17, 35], // Punto del icono que corresponde a la ubicación
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const barIcon = new L.Icon({
  // 👇 Esto le dice al navegador que busque "beer.png" en la misma carpeta
  iconUrl: './../../public/beer.svg',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  
  // Ajusta estos valores también
  iconSize: [25, 41],   
  iconAnchor: [12, 41], 
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
// -------------------------------------------------


// 2. ACEPTAR LA NUEVA PROP onProximitySearch
function Map({ markers, children, onProximitySearch }) {
  const mapCenter = [41.3851, 2.1734];

  return (
    <MapContainer 
      center={mapCenter} 
      zoom={13} 
      className="leaflet-container" 
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {children}

      {markers.map((marker, idx) => {
        if (!marker.latitude || !marker.longitude) {
          console.warn('Marcador omitido por falta de coordenadas:', marker);
          return null;
        }

        const position = [marker.latitude, marker.longitude];
        const isBike = marker.type === 'bike';

        return (
          <Marker 
            key={idx} 
            position={position} 
            icon={isBike ? bikeIcon : barIcon}
          >
            {/* 3. RENDERIZAR EL NUEVO POPUP */}
            <Popup>
              <MarkerPopup 
                marker={marker} 
                onProximitySearch={onProximitySearch}
              />
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}

export default Map;