import process from "node:process";
import { test, expect } from "@playwright/test";

test("create a clinic admin, then rename that admin and use the new login", async ({
  page,
}) => {
  const created = `new_admin_${Date.now()}`;
  const renamed = `${created}_renamed`;
  const password = process.env.CLINIC_TEST_NEW_PASSWORD;
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Add administrator", exact: true })
    .click();
  const createDialog = page.getByRole("dialog", {
    name: "Create administrator account",
  });
  await createDialog.getByLabel(/^Username/).fill(created);
  await createDialog.getByLabel(/^First name/).fill("New");
  await createDialog.getByLabel(/^Last name/).fill("Administrator");
  await createDialog.getByLabel(/^Temporary password/).fill(password);
  await createDialog
    .getByLabel(/^Confirm administrator password/)
    .fill(password);
  await createDialog
    .getByLabel(/^Your current password/)
    .fill("WrongCurrentPassword!123");
  await createDialog
    .getByRole("button", { name: "Create", exact: true })
    .click();
  await expect(createDialog.getByRole("alert")).toContainText(
    "Your current password is incorrect.",
  );
  await createDialog
    .getByLabel(/^Your current password/)
    .fill(process.env.CLINIC_TEST_PASSWORD);
  await createDialog
    .getByRole("button", { name: "Create", exact: true })
    .click();
  await expect(createDialog).toBeHidden();
  await expect(
    page.getByRole("row").filter({ hasText: created }),
  ).toContainText("Administrator");
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await page.getByLabel(/^Username/).fill(created);
  await page.getByLabel(/^Password/).fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Add administrator", exact: true }),
  ).toHaveCount(0);
  expect((await page.request.get("/api/v1/admins/")).status()).toBe(403);
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Settings", exact: true })
    .click();
  await expect(
    page.getByRole("main").getByText("Clinic administrator", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Change username", exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: "Change username" });
  await dialog
    .getByLabel("New username", { exact: true })
    .fill(process.env.CLINIC_TEST_USERNAME);
  await dialog.getByLabel("Current password", { exact: true }).fill(password);
  await dialog
    .getByRole("button", { name: "Update username", exact: true })
    .click();
  await expect(
    dialog.getByText("This username is already in use."),
  ).toBeVisible();
  await dialog.getByLabel("New username", { exact: true }).fill(renamed);
  await dialog
    .getByLabel("Current password", { exact: true })
    .fill("WrongCurrentPassword!123");
  await dialog
    .getByRole("button", { name: "Update username", exact: true })
    .click();
  await expect(
    dialog.getByText("Your current password is incorrect."),
  ).toBeVisible();
  await dialog.getByLabel("Current password", { exact: true }).fill(password);
  await dialog
    .getByRole("button", { name: "Update username", exact: true })
    .click();
  await expect(dialog).toBeHidden();
  await expect(page.locator(".settings-details")).toContainText(renamed);
  const me = await page.request.get("/api/auth/me/");
  expect(me.status()).toBe(200);
  expect((await me.json()).username).toBe(renamed);
  await page.reload();
  await expect(page.locator(".profile")).toContainText(renamed);
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await page.getByLabel(/^Username/).fill(created);
  await page.getByLabel(/^Password/).fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByText("Invalid username or password.")).toBeVisible();
  await page.getByLabel(/^Username/).fill(renamed);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Add administrator", exact: true }),
  ).toHaveCount(0);
});
