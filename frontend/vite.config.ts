import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite dev server proxies /api and /docs to the FastAPI backend on :8000
// so the frontend and backend share a same-origin origin during local dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/docs": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
      "/openapi.json": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});