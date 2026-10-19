import process from "node:process";
import { test, expect } from "@playwright/test";

test("password validation, retained session, and new-password login", async ({
  page,
}) => {
  const original = process.env.CLINIC_TEST_PASSWORD;
  const replacement = process.env.CLINIC_TEST_NEW_PASSWORD;
  if (!replacement)
    throw new Error(
      "Set CLINIC_TEST_NEW_PASSWORD for the isolated password-change account.",
    );
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(original);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Settings", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Change password", exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: "Change password" });
  const current = dialog.getByLabel("Current password", { exact: true });
  const next = dialog.getByLabel("New password", { exact: true });
  const confirm = dialog.getByLabel("Confirm new password", { exact: true });
  const submit = dialog.getByRole("button", { name: "Update password" });
  try {
    await current.fill("IncorrectPassword!789");
    await next.fill(replacement);
    await confirm.fill(replacement);
    await submit.click();
    await expect(
      dialog.getByText("Your current password is incorrect."),
    ).toBeVisible();
    await current.fill(original);
    await confirm.fill("DoesNotMatch!987");
    await submit.click();
    await expect(
      dialog.getByText("The new passwords do not match."),
    ).toBeVisible();
    await next.fill("password");
    await confirm.fill("password");
    await submit.click();
    await expect(dialog.getByText(/This password is too common/)).toBeVisible();
    await next.fill(replacement);
    await confirm.fill(replacement);
    await submit.click();
    await expect(dialog).toBeHidden();
    await expect(
      page.getByText(
        "Password changed. Your other sessions have been signed out.",
      ),
    ).toBeVisible();
    expect((await page.request.get("/api/auth/me/")).status()).toBe(200);
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Dashboard", exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Log out", exact: true }).click();
    await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
    await page.getByLabel(/^Password/).fill(original);
    await page.getByRole("button", { name: "Log in", exact: true }).click();
    await expect(page.getByText("Invalid username or password.")).toBeVisible();
    await page.getByLabel(/^Password/).fill(replacement);
    await page.getByRole("button", { name: "Log in", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Dashboard", exact: true }),
    ).toBeVisible();
  } finally {
    // Restore the isolated test account; never change a user's demo account.
    const csrf = await page.request.get("/api/auth/csrf/");
    const token = (await csrf.json()).csrfToken;
    await page.request.post("/api/auth/password/change/", {
      headers: { "X-CSRFToken": token },
      data: {
        current_password: replacement,
        new_password: original,
        confirm_password: original,
      },
    });
  }
});
