import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Lets every file import from "@/..." instead of counting ../../
    alias: { "@": path.resolve(process.cwd(), "src") },
  },
  server: { port: 5173, open: true },
});
