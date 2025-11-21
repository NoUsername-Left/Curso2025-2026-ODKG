import React from 'react'

// Componente de barra de búsqueda
export default function SearchBar({ searchQuery, setSearchQuery, handleSearch }) {
  return (
    <div className="search-container">
      <form onSubmit={handleSearch} className="flex">
        <input
          type="text"
          placeholder="Buscar por nombre o dirección..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="px-4 py-2 border rounded-l focus:outline-none"
        />
        <button 
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded-r hover:bg-blue-600"
        >
          Buscar
        </button>
      </form>
    </div>
  );
}
