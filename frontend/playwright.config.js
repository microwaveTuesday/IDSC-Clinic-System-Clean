import { defineConfig } from "@playwright/test";
import process from "node:process";
export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 120000,
  expect: { timeout: 15000 },
  use: {
    baseURL: process.env.CLINIC_TEST_BASE_URL || "http://127.0.0.1:5173",
    headless: true,
  },
});
