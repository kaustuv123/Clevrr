# Frontend (React + Vite + TypeScript)

## Run locally
1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the app:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173`.

The frontend calls `POST /api/chat` and renders:
- the app header as `Shopify Analyst`
- clickable sample-question tiles
- dynamic loading stages while the backend is working
- typed response blocks (`text`, `table`)
- response metadata
- sanitized debug traces

The UI does not require a store URL input. Normal usage relies on the backend's configured Shopify store.
