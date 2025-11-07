// src/components/MarkerPopup.jsx (MODIFICADO)

import React from 'react';

export default function MarkerPopup({ marker, onProximitySearch }) {
  
  const isBike = marker.type === 'bike';
  const buttonText = isBike ? "Buscar 3 Bares Cercanos" : "Buscar 3 Bicis Cercanas";

  // Formatear el tipo de bar (ej: "Bars I Pubs Musicals" -> "Bars I Pubs Musicals")
  // Simplemente cogemos el primer tipo si hay varios separados por |
  const barTypeDisplay = (marker.barType || 'Bar').split('|')[0];

  return (
    <div className="popup-content">
      
      <div className="popup-title">
        {marker.displayName || (isBike ? 'Estación' : 'Bar')}
      </div>
      
      {isBike ? (
        <div className="popup-type-station">
          🚲 Estación de Bici (ID: {marker.stationId})
        </div>
      ) : (
        // --- ESTE ES EL CAMBIO ---
        <div className="popup-type-bar">
          {/* Usamos el nuevo 'barTypeDisplay' en lugar de 'Bar' */}
          🍻 {barTypeDisplay}
        </div>
      )}

      <div className="popup-address">
        {marker.displayAddress || 'Sin dirección'}
      </div>

      <button 
        className="proximity-button"
        onClick={() => onProximitySearch(marker)}
      >
        {buttonText}
      </button>
    </div>
  );
}