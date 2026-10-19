import process from "node:process";
import { test, expect } from "@playwright/test";

test("owner manages admins, admin manages staff, staff has no management", async ({
  page,
}) => {
  const suffix = Date.now();
  const adminName = `hierarchy_admin_${suffix}`;
  const renamed = `${adminName}_edited`;
  const staffName = `hierarchy_staff_${suffix}`;
  const password = process.env.CLINIC_TEST_NEW_PASSWORD;
  await page.goto("/");
  async function signIn(username, secret) {
    await expect(
      page.getByRole("button", { name: "Log in", exact: true }),
    ).toBeEnabled();
    await page.getByLabel(/^Username/).fill(username);
    await page.getByLabel(/^Password/).fill(secret);
    await page.getByRole("button", { name: "Log in", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Dashboard", exact: true }),
    ).toBeVisible();
    await expect(page.getByText("Loading clinic data…")).toBeHidden();
  }
  async function manage() {
    await page
      .getByRole("navigation")
      .getByRole("button", { name: "Administration", exact: true })
      .click();
  }
  await signIn(
    process.env.CLINIC_TEST_USERNAME,
    process.env.CLINIC_TEST_PASSWORD,
  );
  await manage();
  await page
    .getByRole("button", { name: "Add administrator", exact: true })
    .click();
  let dialog = page.getByRole("dialog");
  await dialog.getByLabel(/^Username/).fill(adminName);
  await dialog.getByLabel(/^Temporary password/).fill(password);
  await dialog.getByLabel(/^Confirm administrator password/).fill(password);
  await dialog
    .getByLabel(/^Your current password/)
    .fill(process.env.CLINIC_TEST_PASSWORD);
  await dialog.getByRole("button", { name: "Create", exact: true }).click();
  await expect(dialog).toBeHidden();
  await page
    .getByRole("row")
    .filter({ hasText: adminName })
    .getByRole("button", { name: "Edit", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel(/^Username/).fill(renamed);
  await dialog.getByLabel(/^First name/).fill("Owner edited");
  await dialog
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await expect(dialog).toBeHidden();
  await expect(
    page.getByRole("row").filter({ hasText: renamed }),
  ).toContainText("Owner edited");
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await signIn(renamed, password);
  await manage();
  await expect(
    page.getByRole("heading", { name: "Administrators", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Add administrator", exact: true }),
  ).toHaveCount(0);
  expect((await page.request.get("/api/v1/admins/")).status()).toBe(403);
  await page
    .getByRole("button", { name: "Add staff account", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel(/^Username/).fill(staffName);
  await dialog.getByLabel(/^Temporary password/).fill(password);
  await dialog.getByRole("button", { name: "Create", exact: true }).click();
  await expect(dialog).toBeHidden();
  await page
    .getByPlaceholder("Search staff name, username, or email...")
    .fill(staffName);
  let row = page.getByRole("row").filter({ hasText: staffName });
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await dialog.getByLabel(/^First name/).fill("Admin edited");
  await dialog
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await expect(dialog).toBeHidden();
  await expect(row).toContainText("Admin edited");
  await row.getByRole("button", { name: "Deactivate", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(dialog).toBeHidden();
  await expect(row).toContainText("Inactive");
  await row.getByRole("button", { name: "Activate", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(dialog).toBeHidden();
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await signIn(staffName, password);
  await expect(
    page.getByRole("heading", { name: "Dashboard", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("navigation")
      .getByRole("button", { name: "Administration", exact: true }),
  ).toHaveCount(0);
  expect((await page.request.get("/api/v1/users/")).status()).toBe(403);
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await signIn(renamed, password);
  await manage();
  await page
    .getByPlaceholder("Search staff name, username, or email...")
    .fill(staffName);
  row = page.getByRole("row").filter({ hasText: staffName });
  await row.getByRole("button", { name: "Delete", exact: true }).click();
  await dialog.getByLabel(/^Your current password/).fill(password);
  await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(dialog).toBeHidden();
  await expect(row).toHaveCount(0);
});
