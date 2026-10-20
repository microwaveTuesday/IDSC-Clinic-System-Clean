import { test, expect } from "@playwright/test";
import process from "node:process";

test("expired background session clears medical workspace and returns to login", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await page.route("**/api/v1/inventory-notifications/", (route) => route.fulfill({
    status: 401,
    contentType: "application/problem+json",
    body: JSON.stringify({ detail: "Authentication credentials were not provided." }),
  }));
  await expect(page.getByRole("button", { name: "Log in", exact: true })).toBeVisible({ timeout: 15000 });
  await expect(page.getByText("Your session expired. Please log in again.")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Main navigation" })).toHaveCount(0);
});
