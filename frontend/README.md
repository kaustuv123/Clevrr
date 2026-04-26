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
- typed response blocks (`text`, `table`)
- response metadata
- sanitized debug traces
