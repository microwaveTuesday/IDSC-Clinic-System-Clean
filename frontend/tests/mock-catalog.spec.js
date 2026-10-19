import process from "node:process";
import { test, expect } from "@playwright/test";

test("owner edits Registrar status and edits/deletes unused Inventory medicine", async ({
  page,
}) => {
  const suffix = Date.now(),
    sid = `CAT-${suffix}`,
    mid = `CAT-MED-${suffix}`;
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Main navigation" });
  await nav
    .getByRole("button", { name: "Mock Registrar", exact: true })
    .click();
  await page.getByRole("button", { name: "Add student", exact: true }).click();
  await page.getByLabel("Student ID", { exact: true }).fill(sid);
  await page.getByLabel("First name", { exact: true }).fill("Catalog");
  await page.getByLabel("Last name", { exact: true }).fill("Student");
  await page.getByLabel("Course", { exact: true }).fill("BSCS");
  await page.getByLabel("Section", { exact: true }).fill("2B");
  await page.getByRole("button", { name: "Save student", exact: true }).click();
  let row = page.getByRole("row").filter({ hasText: sid });
  await expect(row).toContainText("ACTIVE");
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel("First name", { exact: true }).fill("Registrar edited");
  await page.getByRole("combobox", { name: "Status", exact: true }).selectOption("DROPPED_OUT");
  await page.getByRole("button", { name: "Save student", exact: true }).click();
  await expect(row).toContainText("DROPPED_OUT");
  await nav.getByRole("button", { name: "Students", exact: true }).click();
  await page.getByLabel("Student ID", { exact: true }).fill(sid);
  await page.getByRole("button", { name: "Get student", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Registrar edited Student",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create record", exact: true }),
  ).toBeDisabled();
  await nav
    .getByRole("button", { name: "Mock Inventory", exact: true })
    .click();
  await page.getByRole("button", { name: "Add medicine", exact: true }).click();
  await page.getByLabel("Medicine ID", { exact: true }).fill(mid);
  await page
    .getByLabel("Medicine name", { exact: true })
    .fill("Unused Demo Medicine");
  await page.getByLabel("Generic name", { exact: true }).fill("Demo");
  await page.getByLabel("Unit", { exact: true }).fill("tablet");
  await page.getByLabel("Stock quantity", { exact: true }).fill("0");
  await page
    .getByRole("button", { name: "Save medicine", exact: true })
    .click();
  row = page.getByRole("row").filter({ hasText: mid });
  await expect(row).toContainText("Unused Demo Medicine");
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await page
    .getByLabel("Medicine name", { exact: true })
    .fill("Updated Demo Medicine");
  await page
    .getByRole("button", { name: "Save medicine", exact: true })
    .click();
  await expect(row).toContainText("Updated Demo Medicine");
  await nav
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  await expect(page.getByRole("row").filter({ hasText: mid })).toContainText(
    "Updated Demo Medicine",
  );
  await nav
    .getByRole("button", { name: "Mock Inventory", exact: true })
    .click();
  await row.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog", { name: "Delete Inventory medicine" })
    .getByRole("button", { name: "Confirm deletion", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Delete Inventory medicine" }),
  ).toBeHidden();
  await expect(row).toHaveCount(0);
  await nav
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  await expect(page.getByRole("row").filter({ hasText: mid })).toHaveCount(0);
  await page.screenshot({
    path: "test-results/mock-medicine-notifications.png",
    fullPage: true,
  });
});
