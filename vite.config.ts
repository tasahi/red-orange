import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:1880",
        changeOrigin: true,
      },
      "/comms": {
        target: "ws://localhost:1880",
        ws: true,
      },
    },
  },
});

