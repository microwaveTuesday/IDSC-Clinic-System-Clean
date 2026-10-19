import { test, expect } from "@playwright/test";
import process from "node:process";

test("first Owner setup opens dashboard and permanently becomes shared login", async ({
  page,
  browser,
}) => {
  const username = `first_owner_${Date.now()}`;
  const password = "OwnerRegistration!Secure7392";
  test.skip(
    !process.env.CLINIC_TEST_FIRST_RUN,
    "Requires a freshly migrated isolated database without an Owner.",
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Register the system Owner" }),
  ).toBeVisible();
  await page.getByLabel(/^Username/).fill(username);
  await page.getByLabel(/^Password/).fill(password);
  await page.getByLabel(/^Confirm password/).fill("Mismatch!7392");
  await page.getByRole("button", { name: "Create Owner account" }).click();
  await expect(page.getByText("The passwords do not match.")).toBeVisible();
  await page.getByLabel(/^Confirm password/).fill(password);
  await page.getByRole("button", { name: "Create Owner account" }).click();
  await expect(
    page.getByRole("heading", { name: "Dashboard", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Administration", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Log in", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Register the system Owner" }),
  ).toHaveCount(0);
  await page.getByLabel(/^Username/).fill(username);
  await page.getByLabel(/^Password/).fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Dashboard", exact: true }),
  ).toBeVisible();
  const other = await browser.newContext();
  try {
    const tab = await other.newPage();
    await tab.goto("/");
    await expect(
      tab.getByRole("button", { name: "Log in", exact: true }),
    ).toBeVisible();
    const status = await other.request.get("/api/auth/setup/");
    expect(await status.json()).toEqual({
      owner_registration_available: false,
    });
  } finally {
    await other.close();
  }
});
