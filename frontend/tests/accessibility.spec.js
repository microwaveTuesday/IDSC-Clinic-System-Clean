import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import process from "node:process";

test("responsive clinic pages preserve accessible controls in both themes", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Dashboard", exact: true }),
  ).toBeVisible();
  for (const theme of ["light", "dark"]) {
    const actual = await page.locator("html").getAttribute("data-theme");
    if (actual !== theme)
      await page
        .getByRole("button", { name: `Switch to ${theme} mode`, exact: true })
        .click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    for (const name of [
      "Dashboard",
      "Students",
      "Medicine stock",
      "Settings",
      "Administration",
      "Mock Registrar",
      "Mock Inventory",
    ]) {
      await page
        .getByRole("navigation")
        .getByRole("button", { name, exact: true })
        .click();
      await expect(
        page.getByRole("heading", { name, exact: true }),
      ).toBeVisible();
      const scan = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .analyze();
      expect(
        scan.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          nodes: v.nodes.map((n) => n.target),
        })),
        `${name} ${theme}`,
      ).toEqual([]);
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Settings", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Change password", exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: "Change password" });
  await expect(
    dialog.getByLabel("Current password", { exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});
