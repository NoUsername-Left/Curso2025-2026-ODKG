// Componente de botones de filtro
export default function FilterButtons({ filter, handleFilterChange }) {
  return (
    <div className="filter-container">
      <div className="flex space-x-2">
        <button
          onClick={() => handleFilterChange('all')}
          className={`px-4 py-2 rounded ${filter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Todos
        </button>
        <button
          onClick={() => handleFilterChange('bikes')}
          className={`px-4 py-2 rounded ${filter === 'bikes' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Bicicletas
        </button>
        <button
          onClick={() => handleFilterChange('bars')}
          className={`px-4 py-2 rounded ${filter === 'bars' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Bares
        </button>
      </div>
    </div>
  );
}