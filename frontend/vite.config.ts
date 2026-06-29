import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The whole app is mounted under /weekly_report (matches nginx + FastAPI).
export default defineConfig({
  base: "/weekly_report/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward API + image requests to the FastAPI backend during dev.
      "/weekly_report/api": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
    },
  },
});
