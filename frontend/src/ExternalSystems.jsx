import { useCallback, useEffect, useState } from "react";
import { request } from "./api";

function Input({
  label,
  name,
  value,
  type = "text",
  required = true,
  min,
  max,
}) {
  return (
    <label className="field">
      {label}
      <input
        name={name}
        type={type}
        defaultValue={value ?? ""}
        required={required}
        min={min}
        max={max}
      />
    </label>
  );
}

export function GetStudent({ onFound }) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  return (
    <section className="panel integration-form">
      <h2>Get student from Registrar</h2>
      <p>
        Enter the student ID. Identity, profile and enrollment status come
        directly from Registrar.
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setPending(true);
          setError("");
          try {
            const student = await request("/api/v1/students/import/", "POST", {
              student_id: new FormData(e.currentTarget).get("student_id"),
            });
            await onFound(student);
          } catch (err) {
            setError(err.message);
          } finally {
            setPending(false);
          }
        }}
      >
        <Input label="Student ID" name="student_id" />
        <button className="button primary" disabled={pending}>
          Get student
        </button>
        {error && <p role="alert">{error}</p>}
      </form>
    </section>
  );
}

export function RestockPanel({ medicines, requests, notices, onRefresh }) {
  const [mode, setMode] = useState("ALL");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  return (
    <section className="panel integration-form">
      <h2>Request medicine restock</h2>
      <p>
        Inventory receives the request. Stock changes when Inventory fulfills
        it.
      </p>
      {notices.length > 0 && (
        <div className="notice" role="status">
          <div>
            <strong>Inventory notifications</strong>
            {notices.map((n) => (
              <p key={n.notification_id}>{n.message}</p>
            ))}
            <button
              className="button secondary"
              onClick={async () => {
                try {
                  await request("/api/v1/inventory-notifications/", "POST", {
                    notification_ids: notices.map((n) => n.notification_id),
                  });
                  await onRefresh();
                } catch (e) {
                  setError(e.message);
                }
              }}
            >
              Mark notifications read
            </button>
          </div>
        </div>
      )}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setPending(true);
          setError("");
          setMessage("");
          const form = new FormData(e.currentTarget);
          const items = medicines
            .filter((m) => form.has("select_" + m.medicine_id))
            .map((m) => ({
              medicine_id: m.medicine_id,
              quantity: Number(form.get("qty_" + m.medicine_id)),
            }));
          try {
            await request("/api/v1/restock-requests/", "POST", {
              mode,
              quantity: Number(form.get("quantity") || 100),
              ...(mode === "SELECTED" ? { items } : {}),
            });
            setMessage("Restock request sent to Inventory.");
            await onRefresh();
          } catch (err) {
            setError(err.message);
          } finally {
            setPending(false);
          }
        }}
      >
        <label className="field">
          Restock scope
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="ALL">All active medicines</option>
            <option value="SELECTED">Selected medicines</option>
          </select>
        </label>
        {mode === "ALL" ? (
          <Input
            label="Quantity per medicine"
            name="quantity"
            type="number"
            value="100"
            min="1"
            max="100000"
          />
        ) : (
          medicines
            .filter((m) => m.status === "ACTIVE")
            .map((m) => (
              <div className="restock-choice" key={m.medicine_id}>
                <label>
                  <input type="checkbox" name={"select_" + m.medicine_id} />
                  {m.name} · {m.medicine_id}
                </label>
                <Input
                  label={"Quantity for " + m.name}
                  name={"qty_" + m.medicine_id}
                  type="number"
                  value="100"
                  min="1"
                  max="100000"
                />
              </div>
            ))
        )}
        <button className="button primary" disabled={pending}>
          Send restock request
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <h3>Restock requests</h3>
      {!requests.length && <p>No restock requests yet.</p>}
      {requests.map((r) => (
        <article className="integration-request" key={r.request_id}>
          <strong>
            Request {r.request_id.slice(0, 8)} · {r.status}
          </strong>
          <p>
            {r.items
              .map((i) => `${i.name}: ${i.quantity} ${i.unit}`)
              .join("; ")}
          </p>
        </article>
      ))}
    </section>
  );
}

export function MockWorkspace({ kind, onRefresh }) {
  const registrar = kind === "registrar";
  const base = registrar
    ? "/api/v1/mock/registrar/students/"
    : "/api/v1/mock/inventory/medicines/";
  const key = registrar ? "student_id" : "medicine_id";
  const [rows, setRows] = useState([]);
  const [edit, setEdit] = useState(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [requests, setRequests] = useState([]);
  const [removing, setRemoving] = useState(null);
  const load = useCallback(async () => {
    setRows(await request(base));
    if (!registrar) setRequests(await request("/api/v1/restock-requests/"));
  }, [base, registrar]);
  useEffect(() => {
    let live = true;
    request(base)
      .then((rows) => {
        if (live) setRows(rows);
        return registrar ? [] : request("/api/v1/restock-requests/");
      })
      .then((rows) => {
        if (live) setRequests(rows);
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [base, registrar]);
  async function act(action) {
    if (pending) return false;
    setPending(true);
    setError("");
    try {
      await action();
      await load();
      await onRefresh();
      return true;
    } catch (e) {
      setError(
        e.message +
          (e.body?.errors
            ? " " + Object.values(e.body.errors).flat().join(" ")
            : ""),
      );
      return false;
    } finally {
      setPending(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">MOCK EXTERNAL SYSTEM</div>
          <h1>Mock {registrar ? "Registrar" : "Inventory"}</h1>
          <p>
            Owner-only school-project test workspace. Demo data resets when the
            backend restarts.
          </p>
        </div>
        <button
          className="button primary"
          disabled={pending}
          onClick={() => {
            setError("");
            setEdit({});
          }}
        >
          Add {registrar ? "student" : "medicine"}
        </button>
      </div>
      {error && (
        <div className="notice" role="alert">
          {error}
        </div>
      )}
      {edit && (
        <section className="panel integration-form">
          <h2>
            {edit[key] ? "Edit" : "New"} {registrar ? "student" : "medicine"}
          </h2>
          <form
            key={edit[key] || "new"}
            onSubmit={async (e) => {
              e.preventDefault();
              const data = Object.fromEntries(new FormData(e.currentTarget));
              if (!registrar) {
                data.quantity_in_stock = Number(data.quantity_in_stock);
                data.reorder_level = Number(data.reorder_level);
              }
              const ok = await act(() =>
                request(
                  base + (edit[key] ? encodeURIComponent(edit[key]) + "/" : ""),
                  edit[key] ? "PATCH" : "POST",
                  data,
                ),
              );
              if (ok) setEdit(null);
            }}
          >
            <label className="field">
              {registrar ? "Student ID" : "Medicine ID"}
              <input
                name={key}
                defaultValue={edit[key] || ""}
                readOnly={!!edit[key]}
                required
              />
            </label>
            {(registrar
              ? [
                  ["First name", "first_name"],
                  ["Last name", "last_name"],
                  ["Course", "course"],
                  ["Section", "section"],
                ]
              : [
                  ["Medicine name", "name"],
                  ["Generic name", "generic_name"],
                  ["Unit", "unit"],
                ]
            ).map(([label, name]) => (
              <Input
                key={name}
                label={label}
                name={name}
                value={edit[name]}
                required={name !== "generic_name"}
              />
            ))}
            {!registrar && (
              <>
                <Input
                  label="Stock quantity"
                  name="quantity_in_stock"
                  type="number"
                  value={edit.quantity_in_stock ?? 0}
                  min="0"
                  max="1000000"
                />
                <Input
                  label="Reorder level"
                  name="reorder_level"
                  type="number"
                  value={edit.reorder_level ?? 10}
                  min="0"
                  max="1000000"
                />
              </>
            )}
            <label className="field">
              Status
              <select name="status" defaultValue={edit.status || "ACTIVE"}>
                {(registrar
                  ? ["ACTIVE", "GRADUATED", "DROPPED_OUT", "INACTIVE"]
                  : ["ACTIVE", "INACTIVE"]
                ).map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
            <div className="row-actions">
              <button className="button primary" disabled={pending}>
                Save {registrar ? "student" : "medicine"}
              </button>
              <button
                type="button"
                className="button secondary"
                disabled={pending}
                onClick={() => setEdit(null)}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}
      <section className="panel">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>{registrar ? "Student" : "Medicine"}</th>
                <th>{registrar ? "Course / Section" : "Stock"}</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row[key]}>
                  <td>{row[key]}</td>
                  <td>
                    {registrar
                      ? `${row.first_name} ${row.last_name}`
                      : row.name}
                  </td>
                  <td>
                    {registrar
                      ? `${row.course} / ${row.section}`
                      : `${row.quantity_in_stock} ${row.unit}`}
                  </td>
                  <td>{row.status}</td>
                  <td>
                    <div className="row-actions">
                      <button
                        className="text-link"
                        disabled={pending}
                        onClick={() => {
                          setError("");
                          setEdit(row);
                        }}
                      >
                        Edit
                      </button>
                      {!registrar && (
                        <button
                          className="text-link danger-link"
                          disabled={pending}
                          onClick={() => setRemoving(row)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {removing && (
        <section
          className="panel integration-form"
          role="dialog"
          aria-label="Delete Inventory medicine"
        >
          <h2>Delete {removing.name}?</h2>
          <p>
            This removes the medicine from the mock Inventory catalog and Clinic
            stock list. Medicines with stock transactions must be made inactive
            instead.
          </p>
          <div className="row-actions">
            <button
              className="button danger"
              disabled={pending}
              onClick={async () => {
                if (
                  await act(() =>
                    request(
                      base + encodeURIComponent(removing.medicine_id) + "/",
                      "DELETE",
                    ),
                  )
                )
                  setRemoving(null);
              }}
            >
              Confirm deletion
            </button>
            <button
              className="button secondary"
              disabled={pending}
              onClick={() => setRemoving(null)}
            >
              Cancel
            </button>
          </div>
        </section>
      )}
      {!registrar && (
        <section className="panel integration-form">
          <h2>Incoming restock requests</h2>
          <button
            className="button secondary"
            onClick={() => act(async () => {})}
            disabled={pending}
          >
            Refresh requests
          </button>
          {requests.map((r) => (
            <article className="integration-request" key={r.request_id}>
              <h3>
                Request {r.request_id.slice(0, 8)} · {r.status}
              </h3>
              <p>
                {r.items
                  .map((i) => `${i.name}: ${i.quantity} ${i.unit}`)
                  .join("; ")}
              </p>
              {r.status === "PENDING" && (
                <button
                  className="button primary"
                  disabled={pending}
                  onClick={() =>
                    act(() =>
                      request(
                        `/api/v1/mock/inventory/restock-requests/${r.request_id}/fulfill/`,
                        "POST",
                      ),
                    )
                  }
                >
                  Fulfill request {r.request_id.slice(0, 8)}
                </button>
              )}
            </article>
          ))}
        </section>
      )}
    </>
  );
}
