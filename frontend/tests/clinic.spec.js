import process from "node:process";
import { test, expect } from "@playwright/test";

test("session login, health CRUD, dispensing rollback, reports and logout", async ({
  page,
}) => {
  const runId = Date.now();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Dashboard", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Loading clinic data…")).toBeHidden();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Students", exact: true })
    .click();
  await page
    .getByRole("button", { name: /Juan Dela Cruz/ })
    .first()
    .click();
  await page.getByRole("button", { name: "Create record" }).click();
  await page.getByLabel("Allergies").fill("Integration validation");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Create", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(
    page.getByText("Integration validation", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByText("Loading clinic data…")).toBeHidden();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Students", exact: true })
    .click();
  await page
    .getByRole("button", { name: /Juan Dela Cruz/ })
    .first()
    .click();
  await expect(
    page.getByText("Integration validation", { exact: true }),
  ).toBeVisible();
  await page
    .locator(".record-article")
    .filter({ hasText: "Integration validation" })
    .getByRole("button", { name: "Edit health record" })
    .click();
  await page.getByLabel("Allergies").fill("Updated validation");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(
    page.getByText("Updated validation", { exact: true }),
  ).toBeVisible();
  await page
    .locator(".record-article")
    .filter({ hasText: "Updated validation" })
    .getByRole("button", { name: "Delete health record" })
    .click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(
    page.getByText("Updated validation", { exact: true }),
  ).toBeHidden();
  for (const flow of [
    {
      tab: "Consultations",
      create: "New consultation",
      label: /^Chief complaint/,
      marker: "Visit validation " + runId,
      edit: "Edit consultation",
      del: "Delete consultation",
    },
    {
      tab: "Health status",
      create: "Record status",
      label: /^Remarks/,
      marker: "Status validation " + runId,
      edit: "Edit health status",
      del: "Delete health status",
    },
  ]) {
    await page.getByRole("tab", { name: new RegExp("^" + flow.tab) }).click();
    await page.getByRole("button", { name: flow.create, exact: true }).click();
    await page.getByLabel(flow.label).fill(flow.marker);
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Create", exact: true })
      .click();
    await expect(page.getByRole("dialog")).toBeHidden();
    const article = page
      .locator(".record-article")
      .filter({ hasText: flow.marker });
    await article.getByRole("button", { name: flow.edit }).click();
    await page.getByLabel(flow.label).fill(flow.marker + " updated");
    await page
      .getByRole("button", { name: "Save changes", exact: true })
      .click();
    await expect(page.getByRole("dialog")).toBeHidden();
    await article.getByRole("button", { name: flow.del }).click();
    await page.getByRole("button", { name: "Confirm", exact: true }).click();
    await expect(page.getByRole("dialog")).toBeHidden({ timeout: 30000 });
    await expect(article).toHaveCount(0);
  }
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  await page.locator("form").filter({has: page.getByRole("button", {name: "Dispense", exact: true})}).getByLabel(/^Quantity/).fill("2");
  await page.getByLabel(/^Reason/).fill("Integration validation");
  await page.getByRole("button", { name: "Dispense", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Dispense", exact: true }),
  ).toBeEnabled({ timeout: 30000 });
  await page
    .getByRole("button", { name: "Roll back", exact: true })
    .first()
    .click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 30000 });
  await expect(page.getByText(/ROLLED_BACK/).first()).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Dashboard", exact: true })
    .click();
  await page.getByRole("button", { name: "View report", exact: true }).click();
  await expect(page.locator(".report-summary")).toContainText("total visits");
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Log in", exact: true }),
  ).toBeVisible();
  await expect(
    page.request.get("/api/auth/me/").then((r) => r.status()),
  ).resolves.toBe(401);
  expect(errors).toEqual([]);
});

test("administrator staff management and staff permissions", async ({
  page,
}) => {
  const username = `validation_${Date.now()}`;
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  const nav = page.getByRole("navigation");
  await nav
    .getByRole("button", { name: "Administration", exact: true })
    .click();
  await page.getByRole("button", { name: "Add staff account" }).click();
  await page
    .getByRole("dialog")
    .getByLabel(/^Username/)
    .fill(username);
  await page.getByLabel(/^First name/).fill("Validation");
  await page.getByLabel(/^Last name/).fill("Staff");
  await page
    .getByLabel(/^Temporary password/)
    .fill(process.env.CLINIC_TEST_PASSWORD);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Create", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await page
    .getByPlaceholder("Search staff name, username, or email...")
    .fill(username);
  const row = page.getByRole("row").filter({ hasText: username });
  await row.getByRole("button", { name: "Deactivate", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(row).toContainText("Inactive");
  await row.getByRole("button", { name: "Activate", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(row).toContainText("Active");
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel(/^First name/).fill("Updated");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(row).toContainText("Updated");
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await page.getByLabel(/^Username/).fill(username);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Dashboard", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Loading clinic data…")).toBeHidden();
  await expect(
    nav.getByRole("button", { name: "Administration", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.request.get("/api/v1/users/").then((r) => r.status()),
  ).resolves.toBe(403);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: "test-results/dashboard.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(
    nav.getByRole("button", { name: "Students", exact: true }),
  ).toBeVisible();
  await nav.getByRole("button", { name: "Students", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Students", exact: true }),
  ).toBeVisible();
  await expect
    .poll(() =>
      page
        .locator(".sidebar")
        .evaluate((el) => el.getBoundingClientRect().right),
    )
    .toBeLessThanOrEqual(0);
  await page.screenshot({ path: "test-results/mobile-students.png" });
});
