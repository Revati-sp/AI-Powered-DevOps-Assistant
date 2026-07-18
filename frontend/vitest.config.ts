import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: [
      "tests/unit/**/*.{test,spec}.{ts,tsx}",
      "tests/integration/**/*.{test,spec}.{ts,tsx}",
    ],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["lib/**/*.{ts,tsx}", "features/**/*.{ts,tsx}", "components/**/*.{ts,tsx}"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
