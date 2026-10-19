import process from "node:process";
import { test, expect } from "@playwright/test";

test("staff pages have ten rows and deleting an admin frees its fifth slot", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  const section = page
    .locator("section")
    .filter({
      has: page.getByPlaceholder("Search staff name, username, or email..."),
    });
  const pages = page.getByRole("navigation", { name: "Staff account pages" });
  await expect(section.locator("tbody tr")).toHaveCount(10);
  await expect(pages).toContainText("Page 1 of 2");
  await expect(
    pages.getByRole("button", { name: "Previous", exact: true }),
  ).toBeDisabled();
  await pages.getByRole("button", { name: "Next", exact: true }).click();
  await expect(section.locator("tbody tr")).toHaveCount(1);
  await expect(pages).toContainText("Page 2 of 2");
  await expect(
    pages.getByRole("button", { name: "Next", exact: true }),
  ).toBeDisabled();
  const search = page.getByPlaceholder(
    "Search staff name, username, or email...",
  );
  await search.fill("seedstaff_00");
  await expect(pages).toContainText("Page 1 of 1");
  await expect(section.locator("tbody tr")).toHaveCount(1);
  await search.fill("");
  await pages.getByRole("button", { name: "Next", exact: true }).click();
  await section.getByRole("button", { name: "Delete", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByLabel(/^Your current password/)
    .fill(process.env.CLINIC_TEST_PASSWORD);
  await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(dialog).toBeHidden();
  await expect(pages).toContainText("Page 1 of 1");
  await expect(section.locator("tbody tr")).toHaveCount(10);
  async function api(method, path, data) {
    const token = (await (await page.request.get("/api/auth/csrf/")).json())
      .csrfToken;
    return page.request.fetch(path, {
      method,
      headers: { "X-CSRFToken": token },
      data,
    });
  }
  const ids = [];
  const suffix = Date.now();
  try {
    for (let i = 0; i < 5; i++) {
      const response = await api("POST", "/api/v1/admins/", {
        username: `capacity_${suffix}_${i}`,
        password: process.env.CLINIC_TEST_NEW_PASSWORD,
        confirm_password: process.env.CLINIC_TEST_NEW_PASSWORD,
        current_password: process.env.CLINIC_TEST_PASSWORD,
      });
      expect(response.status()).toBe(201);
      ids.push((await response.json()).user_id);
    }
    await page.reload();
    await page
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("button", { name: "Administration", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Add administrator", exact: true }),
    ).toBeDisabled();
    await expect(page.getByText(/Administrator limit reached/)).toBeVisible();
    let response = await api("POST", "/api/v1/admins/", {
      username: `capacity_${suffix}_sixth`,
      password: process.env.CLINIC_TEST_NEW_PASSWORD,
      confirm_password: process.env.CLINIC_TEST_NEW_PASSWORD,
      current_password: process.env.CLINIC_TEST_PASSWORD,
    });
    expect(response.status()).toBe(409);
    const row = page
      .getByRole("row")
      .filter({ hasText: `capacity_${suffix}_0` });
    await row.getByRole("button", { name: "Deactivate", exact: true }).click();
    await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(dialog).toBeHidden();
    await expect(
      page.getByRole("button", { name: "Add administrator", exact: true }),
    ).toBeDisabled();
    await row.getByRole("button", { name: "Delete", exact: true }).click();
    await dialog
      .getByLabel(/^Your current password/)
      .fill(process.env.CLINIC_TEST_PASSWORD);
    await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(dialog).toBeHidden();
    ids.shift();
    await expect(
      page.getByRole("button", { name: "Add administrator", exact: true }),
    ).toBeEnabled();
    response = await api("POST", "/api/v1/admins/", {
      username: `capacity_${suffix}_replacement`,
      password: process.env.CLINIC_TEST_NEW_PASSWORD,
      confirm_password: process.env.CLINIC_TEST_NEW_PASSWORD,
      current_password: process.env.CLINIC_TEST_PASSWORD,
    });
    expect(response.status()).toBe(201);
    ids.push((await response.json()).user_id);
  } finally {
    for (const id of ids)
      await api("DELETE", `/api/v1/admins/${id}/`, {
        current_password: process.env.CLINIC_TEST_PASSWORD,
      });
  }
});
