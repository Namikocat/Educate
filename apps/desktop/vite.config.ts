import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Content packages live in /subjects and are bundled into the app at build time (offline-first).
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  resolve: {
    alias: {
      "@subjects": path.resolve(__dirname, "../../subjects"),
      "@viz": path.resolve(__dirname, "../../packages/visualization-core/src"),
      "@assess": path.resolve(__dirname, "../../packages/assessment-core/src"),
      "@curriculum": path.resolve(__dirname, "../../packages/curriculum-core/src"),
    },
  },
  server: { port: 1420, strictPort: true, fs: { allow: [path.resolve(__dirname, "../..")] } },
  build: { target: "es2021", chunkSizeWarningLimit: 1500 },
  test: { include: ["tests/**/*.test.ts", "../../packages/**/tests/*.test.ts"] },
});
