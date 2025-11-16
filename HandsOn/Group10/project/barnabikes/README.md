# Barnabikes

Proyecto web para visualizar estaciones de bicicletas y bares en Barcelona sobre un mapa interactivo.

## Estructura
- `frontend/` — Aplicación React (Vite)
- `backend/` — API Node.js/Express (conexión a GraphDB)

## Instalación

### 1. Instalar dependencias
```bash
cd frontend
npm install
cd ../backend
npm install
```

### 2. Ejecutar el backend
```bash
npm start
```

### 3. Ejecutar el frontend
En otra terminal:
```bash
cd frontend
npm run dev
```

El frontend estará en http://localhost:5173 y el backend en http://localhost:4000

## Personalización
- Modifica los endpoints y queries SPARQL en `backend/server.js` según tu ontología/datos.
- El diseño y componentes se encuentran en `frontend/src/`.
