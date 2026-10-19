import { test, expect } from "@playwright/test";

test("password typing retains focus across refresh; keyboard close uses current pending state", async ({
  page,
}) => {
  let studentReads = 0,
    finishUpdate;
  const updateGate = new Promise((resolve) => {
    finishUpdate = resolve;
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/password/change/") {
      await updateGate;
      return route.fulfill({
        status: 400,
        json: {
          detail: "Test validation response.",
          errors: { current_password: ["Test current password rejected."] },
        },
      });
    }
    let data = [];
    if (path === "/api/auth/setup/")
      data = { owner_registration_available: false };
    if (path === "/api/auth/me/")
      data = {
        id: 999,
        username: "focus_test_owner",
        email: "",
        is_staff: true,
        role: "OWNER",
      };
    else if (path === "/api/auth/csrf/") data = { csrfToken: "test-token" };
    else if (path === "/api/v1/dashboard/")
      data = {
        summary: {
          total_students: 0,
          total_health_records: 0,
          total_medicine_stock: 0,
          low_stock_medicines: 0,
        },
        recent_activity: [],
      };
    if (path === "/api/v1/students/") studentReads++;
    await route.fulfill({ json: data });
  });
  await page.goto("/");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Settings", exact: true })
    .click();
  const open = page.getByRole("button", {
    name: "Change password",
    exact: true,
  });
  await open.click();
  const dialog = page.getByRole("dialog", { name: "Change password" });
  const current = dialog.getByLabel("Current password", { exact: true });
  const next = dialog.getByLabel("New password", { exact: true });
  const confirm = dialog.getByLabel("Confirm new password", { exact: true });
  await expect(current).toBeFocused();
  await current.fill("FakeCurrent!987");
  await next.focus();
  const before = studentReads;
  let typed = "";
  for (const char of "TypingPass!987") {
    await next.pressSequentially(char, { delay: 600 });
    typed += char;
    await expect(next).toBeFocused();
    await expect(next).toHaveValue(typed);
  }
  await expect.poll(() => studentReads).toBeGreaterThan(before);
  await confirm.fill(typed);
  const submit = dialog.getByRole("button", {
    name: "Update password",
    exact: true,
  });
  await submit.focus();
  await page.keyboard.press("Tab");
  await expect(
    dialog.getByRole("button", { name: "Close dialog" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(submit).toBeFocused();
  await submit.click();
  await expect(dialog.locator("form")).toHaveAttribute("aria-busy", "true");
  await page.keyboard.press("Escape");
  await expect(dialog).toBeVisible();
  finishUpdate();
  await expect(dialog.getByRole("alert").first()).toBeVisible();
  await expect(dialog.locator("form")).toHaveAttribute("aria-busy", "false");
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(open).toBeFocused();
});
