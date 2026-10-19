import process from "node:process";
import { test, expect } from "@playwright/test";

test("Registrar sync, gapless labels, inventory delivery and deletion permissions", async ({
  page,
  browser,
}) => {
  test.setTimeout(180000);
  const suffix = Date.now(),
    sid = `DEMO-${suffix}`,
    mid = `DEMO-MED-${suffix}`;
  const base = process.env.CLINIC_TEST_BASE_URL || "http://127.0.0.1:5173";
  const nav = page.getByRole("navigation", { name: "Main navigation" });
  async function write(path, data = {}, method = "POST") {
    const token = (await (await page.request.get("/api/auth/csrf/")).json())
      .csrfToken;
    const response = await page.request.fetch("/api/v1/" + path, {
      method,
      headers: { "X-CSRFToken": token },
      data,
    });
    expect(response.status()).toBeLessThan(300);
    return response.status() === 204 ? null : response.json();
  }
  await page.goto("/");
  await page.getByLabel(/^Username/).fill(process.env.CLINIC_TEST_USERNAME);
  await page.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await nav
    .getByRole("button", { name: "Mock Registrar", exact: true })
    .click();
  await page.getByRole("button", { name: "Add student", exact: true }).click();
  await page.getByLabel("Student ID", { exact: true }).fill(sid);
  await page.getByLabel("First name", { exact: true }).fill("Workflow");
  await page.getByLabel("Last name", { exact: true }).fill("Student");
  await page.getByLabel("Course", { exact: true }).fill("BSIT");
  await page.getByLabel("Section", { exact: true }).fill("1A");
  await page.getByRole("button", { name: "Save student", exact: true }).click();
  await expect(page.getByRole("row").filter({ hasText: sid })).toContainText(
    "Workflow Student",
  );
  const ids = [];
  for (let i = 0; i < 3; i++) {
    const r = await write("health-records/", {
      student_id: sid,
      blood_type: "O+",
      allergies: "Number test",
    });
    ids.push(r.health_record_id);
  }
  for (const id of ids) await write(`health-records/${id}/`, {}, "DELETE");
  const record = await write("health-records/", {
    student_id: sid,
    blood_type: "O+",
    allergies: "Replacement record",
  });
  expect(record.health_record_id).toBeGreaterThan(ids[2]);
  const visits = [];
  for (let i = 0; i < 3; i++) {
    const r = await write("consultations/", {
      student_id: sid,
      chief_complaint: "Visit number test",
    });
    visits.push(r.consultation_id);
  }
  for (const id of visits) await write(`consultations/${id}/`, {}, "DELETE");
  await write("consultations/", {
    student_id: sid,
    chief_complaint: "Replacement visit",
  });
  await page.reload();
  await nav.getByRole("button", { name: "Students", exact: true }).click();
  await page.getByLabel("Student ID", { exact: true }).fill(sid);
  await page.getByRole("button", { name: "Get student", exact: true }).click();
  await expect(
    page.getByText("Health record #1", { exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: /Consultations/ }).click();
  await expect(page.locator(".visit-date")).toContainText("#1");
  const staff = await write("users/", {
    username: `external_staff_${suffix}`,
    password: process.env.CLINIC_TEST_NEW_PASSWORD,
  });
  const ctx = await browser.newContext();
  const sp = await ctx.newPage();
  await sp.goto(base);
  await sp.getByLabel(/^Username/).fill(staff.username);
  await sp.getByLabel(/^Password/).fill(process.env.CLINIC_TEST_NEW_PASSWORD);
  await sp.getByRole("button", { name: "Log in", exact: true }).click();
  await sp
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Students", exact: true })
    .click();
  await sp.getByLabel("Student ID", { exact: true }).fill(sid);
  await sp.getByRole("button", { name: "Get student", exact: true }).click();
  await expect(
    sp.getByRole("button", { name: "Delete health record", exact: true }),
  ).toHaveCount(0);
  await expect(
    sp
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("button", { name: "Mock Registrar", exact: true }),
  ).toHaveCount(0);
  await write(
    `mock/registrar/students/${sid}/`,
    { first_name: "Updated", status: "GRADUATED" },
    "PATCH",
  );
  await expect(
    sp.getByRole("heading", { name: "Updated Student", exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await expect(
    sp.getByRole("button", { name: "Create record", exact: true }),
  ).toBeDisabled();
  await write(
    `mock/registrar/students/${sid}/`,
    { status: "DROPPED_OUT" },
    "PATCH",
  );
  await expect(sp.getByText("Dropped out", { exact: true })).toBeVisible({
    timeout: 15000,
  });
  await write(`mock/registrar/students/${sid}/`, { status: "ACTIVE" }, "PATCH");
  await nav
    .getByRole("button", { name: "Mock Inventory", exact: true })
    .click();
  await page.getByRole("button", { name: "Add medicine", exact: true }).click();
  await page.getByLabel("Medicine ID", { exact: true }).fill(mid);
  await page
    .getByLabel("Medicine name", { exact: true })
    .fill("Workflow Medicine");
  await page.getByLabel("Generic name", { exact: true }).fill("Test");
  await page.getByLabel("Unit", { exact: true }).fill("tablet");
  await page.getByLabel("Stock quantity", { exact: true }).fill("10");
  await page
    .getByRole("button", { name: "Save medicine", exact: true })
    .click();
  await expect(page.getByRole("row").filter({ hasText: mid })).toContainText(
    "Workflow Medicine",
  );
  await nav
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  await expect(
    page.getByText(/Inventory added Workflow Medicine/).first(),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Restock scope", exact: true })
    .selectOption("SELECTED");
  await page
    .locator(".restock-choice")
    .filter({ hasText: mid })
    .locator("input[type=checkbox]")
    .check();
  await page.locator(".restock-choice").filter({hasText: mid}).getByRole("spinbutton")
    .fill("7");
  await page
    .getByRole("button", { name: "Send restock request", exact: true })
    .click();
  await expect(
    page.getByText("Restock request sent to Inventory.", { exact: true }),
  ).toBeVisible();
  let requests = await (
    await page.request.get("/api/v1/restock-requests/")
  ).json();
  let delivery = requests[0];
  expect(
    (await (await page.request.get(`/api/v1/medicines/${mid}/`)).json())
      .quantity_in_stock,
  ).toBe(10);
  await nav
    .getByRole("button", { name: "Mock Inventory", exact: true })
    .click();
  await page
    .getByRole("button", {
      name: `Fulfill request ${delivery.request_id.slice(0, 8)}`,
      exact: true,
    })
    .click();
  await expect(
    page
      .locator(".integration-request")
      .filter({ hasText: delivery.request_id.slice(0, 8) }),
  ).toContainText("FULFILLED");
  expect(
    (await (await page.request.get(`/api/v1/medicines/${mid}/`)).json())
      .quantity_in_stock,
  ).toBe(17);
  await nav
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  await page.getByRole("combobox", { name: "Restock scope", exact: true }).selectOption("ALL");
  await page.getByLabel("Quantity per medicine", { exact: true }).fill("2");
  await page
    .getByRole("button", { name: "Send restock request", exact: true })
    .click();
  await expect(
    page.getByText("Restock request sent to Inventory.", { exact: true }),
  ).toBeVisible();
  requests = await (await page.request.get("/api/v1/restock-requests/")).json();
  delivery = requests[0];
  await write(
    `mock/inventory/restock-requests/${delivery.request_id}/fulfill/`,
  );
  const disp = await write("medicine-dispensations/", {
    student_id: sid,
    medicine_id: mid,
    quantity: 1,
    reason: "History deletion",
  });
  await page.reload();
  await nav
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  const history = page
    .locator(".settings-option")
    .filter({ hasText: `#${disp.dispensation_id} · ${sid}` });
  await history
    .getByRole("button", { name: "Delete dispensing history", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(history).toHaveCount(0);
  expect(
    (await (await page.request.get(`/api/v1/medicines/${mid}/`)).json())
      .quantity_in_stock,
  ).toBe(18);
  await sp
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Medicine stock", exact: true })
    .click();
  await expect(
    sp.getByRole("button", { name: "Delete dispensing history", exact: true }),
  ).toHaveCount(0);
  await ctx.close();
  await write(
    `users/${staff.user_id}/`,
    { current_password: process.env.CLINIC_TEST_PASSWORD },
    "DELETE",
  );
});
