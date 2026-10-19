import process from "node:process";
import { test, expect } from "@playwright/test";

test("deactivate, reactivate and delete administrator and staff accounts", async ({
  page,
}) => {
  const suffix = Date.now();
  const adminName = `lifecycle_admin_${suffix}`;
  const staffName = `lifecycle_staff_${suffix}`;
  const original = process.env.CLINIC_TEST_PASSWORD;
  const password = process.env.CLINIC_TEST_NEW_PASSWORD;
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(original);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  async function post(path, data) {
    const token = (await (await page.request.get("/api/auth/csrf/")).json())
      .csrfToken;
    return page.request.post(path, { headers: { "X-CSRFToken": token }, data });
  }
  const admin = await post("/api/v1/admins/", {
    username: adminName,
    password,
    confirm_password: password,
    current_password: original,
  });
  expect(admin.status()).toBe(201);
  const staff = await post("/api/v1/users/", { username: staffName, password });
  expect(staff.status()).toBe(201);
  await page.reload();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  // Owner accounts are kept out of both manageable directories.
  await expect(
    page.getByRole("row").filter({ hasText: process.env.CLINIC_TEST_USERNAME }),
  ).toHaveCount(0);
  for (const username of [adminName, staffName]) {
    if (username === staffName)
      await page
        .getByPlaceholder("Search staff name, username, or email...")
        .fill(username);
    const row = page.getByRole("row").filter({ hasText: username });
    await row.getByRole("button", { name: "Deactivate", exact: true }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Cancel", exact: true })
      .click();
    await expect(row).toContainText("Active");
    await row.getByRole("button", { name: "Deactivate", exact: true }).click();
    await page.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(page.getByRole("dialog")).toBeHidden();
    await expect(row).toContainText("Inactive");
    // Separate request context: failed victim login must not replace the actor's session.
    const probe = await page.context().browser().newContext();
    const csrf = (
      await (
        await probe.request.get(
          `${process.env.CLINIC_TEST_BASE_URL || "http://127.0.0.1:5173"}/api/auth/csrf/`,
        )
      ).json()
    ).csrfToken;
    const login = await probe.request.post(
      `${process.env.CLINIC_TEST_BASE_URL || "http://127.0.0.1:5173"}/api/auth/login/`,
      { headers: { "X-CSRFToken": csrf }, data: { username, password } },
    );
    expect(login.status()).toBe(401);
    await probe.close();
    await row.getByRole("button", { name: "Activate", exact: true }).click();
    await page.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(page.getByRole("dialog")).toBeHidden();
    await expect(row).toContainText("Active");
    await row.getByRole("button", { name: "Delete", exact: true }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("This cannot be undone");
    await dialog.getByLabel(/^Your current password/).fill("WrongPassword!123");
    await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(dialog.getByRole("alert")).toContainText(
      "Your current password is incorrect",
    );
    await dialog.getByLabel(/^Your current password/).fill(original);
    await dialog.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(dialog).toBeHidden();
    await expect(row).toHaveCount(0);
    await page.reload();
    await page
      .getByRole("navigation")
      .getByRole("button", { name: "Administration", exact: true })
      .click();
    await expect(
      page.getByRole("row").filter({ hasText: username }),
    ).toHaveCount(0);
  }
});
