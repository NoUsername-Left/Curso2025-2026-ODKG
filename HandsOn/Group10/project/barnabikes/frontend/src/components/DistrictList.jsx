import React from 'react';

export default function DistrictList({ districts, selectedDistrict, onDistrictClick }) {
  
  return (
    <div className="district-list">
      <h3>Distritos</h3>
      
      {/* Botón para mostrar todos */}
      <button
        onClick={() => onDistrictClick('all')}
        className={`district-button ${selectedDistrict === 'all' ? 'active' : ''}`}
      >
        Mostrar Todos
      </button>

      {/* Lista de distritos desde la API */}
      {districts.map(districtName => (
        <button
          key={districtName}
          onClick={() => onDistrictClick(districtName)}
          className={`district-button ${selectedDistrict === districtName ? 'active' : ''}`}
        >
          {districtName}
        </button>
      ))}
    </div>
  );
}