import {
  PasswordChangeDialog,
  UsernameChangeDialog,
} from "./CredentialDialogs";
import OwnerRegistration from "./OwnerRegistration";
import { GetStudent, RestockPanel, MockWorkspace } from "./ExternalSystems";
import { useCallback, useEffect, useState } from "react";
import { request, listAll } from "./api";
import {
  Icon,
  Logo,
  Badge,
  Button,
  Search,
  Empty,
  Modal,
  Field,
} from "./ClinicUI";
const date = (value, time = false) =>
  new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Manila",
    month: "short",
    day: "numeric",
    year: time ? undefined : "numeric",
    ...(time ? { hour: "numeric", minute: "2-digit" } : {}),
  }).format(new Date(value));
const fullname = (student) => `${student.first_name} ${student.last_name}`;
const activityLabels = {
  CONSULTATION: "Consultation recorded",
  HEALTH_RECORD: "Health record created",
  HEALTH_STATUS: "Health status recorded",
  MEDICINE_DISPENSATION: "Medicine dispensed",
  MEDICINE_DISPENSATION_ROLLBACK: "Dispensation rolled back",
};
function ThemeToggle({ dark, onToggle }) {
  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={onToggle}
      aria-label={`Switch to ${dark ? "light" : "dark"} mode`}
      aria-pressed={dark}
      title={`Switch to ${dark ? "light" : "dark"} mode`}
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        {dark ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" />
          </>
        ) : (
          <path d="M20.5 13.3A8.5 8.5 0 0 1 10.7 3.5a8.5 8.5 0 1 0 9.8 9.8Z" />
        )}
      </svg>
      <span>{dark ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}
export default function App() {
  const [dark, setDark] = useState(
    () => document.documentElement.dataset.theme === "dark",
  );
  useEffect(() => {
    const theme = dark ? "dark" : "light";
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("clinic-theme", theme);
    } catch {
      /* Theme still works when browser storage is unavailable. */
    }
  }, [dark]);
  const themeToggle = (
    <ThemeToggle dark={dark} onToggle={() => setDark((value) => !value)} />
  );
  const [session, setSession] = useState(null);
  const [students, setStudents] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [summary, setSummary] = useState({
    total_students: 0,
    total_health_records: 0,
    total_medicine_stock: 0,
    low_stock_medicines: 0,
  });
  const [admin, setAdmin] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [dispensations, setDispensations] = useState([]);
  const [report, setReport] = useState(null);
  const [page, setPage] = useState("dashboard");
  const [loggedIn, setLoggedIn] = useState(false);
  const [ownerSetup, setOwnerSetup] = useState(null);
  const [selected, setSelected] = useState(null);
  const [records, setRecords] = useState([]);
  const [visits, setVisits] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [users, setUsers] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [staffPage, setStaffPage] = useState(1);
  const [restockRequests, setRestockRequests] = useState([]);
  const [inventoryNotices, setInventoryNotices] = useState([]);
  const [activities, setActivities] = useState([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [tab, setTab] = useState("Health record");
  const [editor, setEditor] = useState(null);
  const [confirmation, setConfirmation] = useState(null);
  const [medicine, setMedicine] = useState(null);
  const [toast, setToast] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [info, setInfo] = useState("");
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [usernameOpen, setUsernameOpen] = useState(false);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(""), 4500);
      return () => clearTimeout(t);
    }
  }, [toast]);
  function navigate(next) {
    setStaffPage(1);
    setPage(next);
    setSelected(null);
    setSearch("");
    setFilter("All");
    setMenuOpen(false);
  }
  function openStudent(s) {
    setSelected(s);
    setPage("students");
    setTab("Health record");
    setSearch("");
  }
  const navigation = [
    { id: "dashboard", label: "Dashboard", icon: "grid" },
    { id: "students", label: "Students", icon: "students" },
    { id: "medicines", label: "Medicine stock", icon: "pill" },
    { id: "settings", label: "Settings", icon: "settings" },
    { id: "admin", label: "Administration", icon: "shield" },
    { id: "registrar", label: "Mock Registrar", icon: "students" },
    { id: "inventory", label: "Mock Inventory", icon: "pill" },
  ];
  const refreshAccounts = useCallback(async () => {
    try {
      const staff = await listAll("users");
      let administrators = [];
      try {
        administrators = await listAll("admins");
      } catch (error) {
        if (error.status !== 403) throw error;
      }
      setUsers(staff);
      setStaffPage((current) =>
        Math.min(current, Math.max(1, Math.ceil(staff.length / 10))),
      );
      setAdmins(administrators);
      setAdmin(true);
    } catch (e) {
      if (e.status !== 403) throw e;
      setUsers([]);
      setAdmins([]);
      setAdmin(false);
    }
  }, []);
  const refresh = useCallback(async () => {
    const [ss, mm, rr, vv, hh, dd, dashboard] = await Promise.all([
      listAll("students"),
      listAll("medicines"),
      listAll("health-records"),
      listAll("consultations"),
      listAll("health-statuses"),
      listAll("medicine-dispensations"),
      request("/api/v1/dashboard/"),
    ]);
    setStudents(ss);
    setMedicines(mm);
    setRecords(rr);
    setVisits(vv);
    setStatuses(hh);
    setDispensations(dd);
    setSummary(dashboard.summary);
    setActivities(dashboard.recent_activity);
    await refreshAccounts();
  }, [refreshAccounts]);
  useEffect(() => {
    let active = true;
    request("/api/auth/setup/")
      .then((status) => {
        if (!active) return null;
        const available = status.owner_registration_available === true;
        setOwnerSetup(available);
        return available ? null : request("/api/auth/me/");
      })
      .then(async (user) => {
        if (active && user) {
          setSession(user);
          setLoggedIn(true);
          await refresh();
        }
      })
      .catch((e) => {
        if (active && e.status !== 401) {
          setLoginError(e.message);
          setError(e.message);
        }
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [refresh]);
  const refreshExternal = useCallback(async () => {
    const [ss, mm, nn, rr] = await Promise.all([
      listAll("students"),
      listAll("medicines"),
      request("/api/v1/inventory-notifications/"),
      request("/api/v1/restock-requests/"),
    ]);
    setStudents(ss);
    setMedicines(mm);
    setInventoryNotices(nn);
    setRestockRequests(rr);
    setSelected((current) =>
      current
        ? ss.find((s) => s.student_id === current.student_id) || current
        : null,
    );
  }, []);
  useEffect(() => {
    if (!loggedIn) return;
    let active = true;
    let running = false;
    const sync = async () => {
      if (!active || running) return;
      running = true;
      try {
        await refreshExternal();
      } catch {
        /* Existing data stays visible during temporary integration failures. */
      } finally {
        running = false;
      }
    };
    sync();
    const timer = setInterval(sync, 5000);
    window.addEventListener("focus", sync);
    return () => {
      active = false;
      clearInterval(timer);
      window.removeEventListener("focus", sync);
    };
  }, [loggedIn, refreshExternal]);
  function clearSession() {
    setPasswordOpen(false);
    setUsernameOpen(false);
    setAdmins([]);
    setLoggedIn(false);
    setSession(null);
    setStudents([]);
    setRecords([]);
    setVisits([]);
    setStatuses([]);
    setMedicines([]);
    setUsers([]);
    setDispensations([]);
    setSelected(null);
    setEditor(null);
    setReport(null);
    setMenuOpen(false);
    setAdmin(false);
    setConfirmation(null);
    setMedicine(null);
    setInfo("");
    setToast("");
    setActivities([]);
    setSummary({
      total_students: 0,
      total_health_records: 0,
      total_medicine_stock: 0,
      low_stock_medicines: 0,
    });
  }
  async function act(action, update = refresh) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await action();
      try {
        await update();
        setToast("Changes saved.");
      } catch (e) {
        setError(
          "The change was saved, but refreshing failed. Please reload to see the latest data. " +
            e.message,
        );
        if (e.status === 401) clearSession();
      }
      return true;
    } catch (e) {
      setError(
        e.message +
          (e.body?.errors
            ? " " + Object.values(e.body.errors).flat().join(" ")
            : ""),
      );
      if (e.status === 401) {
        clearSession();
      }
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function saveEditor(e) {
    e.preventDefault();
    const form = Object.fromEntries(new FormData(e.currentTarget));
    const resources = {
      record: ["health-records", "health_record_id"],
      consultation: ["consultations", "consultation_id"],
      status: ["health-statuses", "status_id"],
      user: ["users", "user_id"],
      admin: ["admins", "user_id"],
    };
    const [resource, key] = resources[editor.kind];
    if (!["user", "admin"].includes(editor.kind))
      form.student_id = selected.student_id;
    if (editor.kind === "record") {
      for (const key of ["height_cm", "weight_kg"])
        form[key] = form[key] ? Number(form[key]) : null;
    }
    const existing = editor.existing;
    if (
      await act(
        () =>
          request(
            "/api/v1/" + resource + "/" + (existing ? existing[key] + "/" : ""),
            existing ? "PATCH" : "POST",
            form,
            { version: existing?.updated_at },
          ),
        ["user", "admin"].includes(editor.kind) ? refreshAccounts : refresh,
      )
    )
      setEditor(null);
  }
  function deleteRecord(kind, id) {
    setError("");
    const resource = {
      record: "health-records",
      consultation: "consultations",
      status: "health-statuses",
    }[kind];
    setConfirmation({
      title: "Delete this " + kind + "?",
      action: () =>
        act(() => request("/api/v1/" + resource + "/" + id + "/", "DELETE")),
    });
  }
  function confirmAccountAction(resource, account, action) {
    setError("");
    const deleting = action === "delete";
    setConfirmation({
      title: `${deleting ? "Delete" : action === "activate" ? "Activate" : "Deactivate"} ${account.username}?`,
      requiresPassword: deleting,
      description: deleting
        ? "Permanently delete this sign-in account? This cannot be undone. Clinic medical records will remain. Enter your current password to confirm."
        : action === "activate"
          ? "Allow this account to sign in again? Previously signed-in sessions will stay signed out."
          : "Prevent this account from signing in and sign out its existing sessions? You can activate it again later.",
      action: (password) =>
        act(
          () =>
            request(
              `/api/v1/${resource}/${account.user_id}/${deleting ? "" : action + "/"}`,
              deleting ? "DELETE" : "POST",
              deleting ? { current_password: password } : undefined,
            ),
          refreshAccounts,
        ),
    });
  }
  const title = selected
    ? "Student health record"
    : navigation.find((n) => n.id === page).label;
  const sampleSummary = summary;
  const lowStock = medicines.filter((m) => m.is_low_stock);
  const studentRecords = records.filter(
    (r) => r.student_id === selected?.student_id,
  );
  const studentVisits = visits.filter(
    (r) =>
      r.student_id === selected?.student_id &&
      `${r.chief_complaint} ${r.assessment} ${r.treatment} ${r.notes}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const studentStatuses = statuses.filter(
    (r) => r.student_id === selected?.student_id,
  );
  const filteredStudents = students.filter(
    (s) =>
      `${fullname(s)} ${s.student_id} ${s.course} ${s.section}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (filter === "All" || s.course === filter),
  );
  const filteredMedicines = medicines.filter(
    (m) =>
      `${m.name} ${m.generic_name} ${m.medicine_id}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (filter === "All" ||
        (filter === "Low stock" ? m.is_low_stock : m.quantity_in_stock > 0)),
  );
  const filteredUsers = users.filter((u) =>
    `${u.username} ${u.first_name} ${u.last_name} ${u.email}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  const staffTotalPages = Math.max(1, Math.ceil(filteredUsers.length / 10));
  const currentStaffPage = Math.min(staffPage, staffTotalPages);
  const visibleStaff = filteredUsers.slice(
    (currentStaffPage - 1) * 10,
    currentStaffPage * 10,
  );
  const adminLimitReached = admins.length >= 5;
  if (!loggedIn && ownerSetup === null)
    return (
      <div className="login-page">
        <div className="login-form-wrap">
          <div className="login-form">
            <Logo />
            <p role="status">
              {busy ? "Checking system setup…" : "Unable to load sign-in."}
            </p>
            {loginError && <p role="alert">{loginError}</p>}
            {!busy && (
              <Button onClick={() => window.location.reload()}>Retry</Button>
            )}
          </div>
        </div>
      </div>
    );
  if (!loggedIn && ownerSetup)
    return (
      <div className="login-page">
        <div className="login-theme">{themeToggle}</div>
        <div className="login-form-wrap">
          <div className="login-brand">
            <Logo />
          </div>
          <OwnerRegistration
            onAlreadyRegistered={() => {
              setOwnerSetup(false);
              setLoginError(
                "Owner registration is already complete. Please log in.",
              );
            }}
            onComplete={async (user) => {
              setOwnerSetup(false);
              setSession(user);
              navigate("dashboard");
              setLoggedIn(true);
              try {
                await refresh();
              } catch (e) {
                setError(
                  "Owner created, but loading the workspace failed. Please refresh. " +
                    e.message,
                );
              }
            }}
          />
        </div>
      </div>
    );
  if (!loggedIn)
    return (
      <div className="login-page">
        <div className="login-theme">{themeToggle}</div>
        <div className="login-form-wrap">
          <form
            className="login-form"
            onSubmit={async (e) => {
              e.preventDefault();
              const credentials = new FormData(e.currentTarget);
              setLoginError("");
              setBusy(true);
              try {
                const data = await request("/api/auth/login/", "POST", {
                  username: credentials.get("email"),
                  password: credentials.get("password"),
                });
                setSession(data.user);
                navigate("dashboard");
                setLoggedIn(true);
                await refresh();
              } catch (e) {
                setLoginError(e.message);
                setError(e.message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <div className="login-brand">
              <Logo />
            </div>
            <span className="eyebrow">WELCOME BACK</span>
            <h2>Log in to your account</h2>
            <p>Owner, Admin and Staff sign in here.</p>
            <Field label="Username" name="email" required />
            <Field label="Password" name="password" type="password" required />
            <div className="login-forgot-row">
              <button className="text-link" type="button" disabled>
                Forgot password?
              </button>
            </div>
            {loginError && (
              <div className="notice" role="alert">
                {loginError}
              </div>
            )}
            <Button type="submit" icon="arrow" disabled={busy}>
              Log in
            </Button>
          </form>
        </div>
      </div>
    );
  return (
    <div className="app-shell" aria-busy={busy}>
      {menuOpen && (
        <div className="sidebar-scrim" onClick={() => setMenuOpen(false)} />
      )}
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <Logo />
        <div className="workspace-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.slice(0, 3).map((n) => (
            <button
              key={n.id}
              className={`nav-item ${page === n.id ? "active" : ""}`}
              onClick={() => navigate(n.id)}
            >
              <Icon name={n.icon} />
              <span>{n.label}</span>
              {page === n.id && <i />}
            </button>
          ))}
          <div className="nav-divider" />
          <div className="workspace-label">MANAGEMENT</div>
          {navigation
            .slice(3)
            .filter(
              (n) =>
                (n.id !== "admin" || admin) &&
                (!["registrar", "inventory"].includes(n.id) ||
                  session?.role === "OWNER"),
            )
            .map((n) => (
              <button
                key={n.id}
                className={`nav-item ${page === n.id ? "active" : ""}`}
                onClick={() => navigate(n.id)}
              >
                <Icon name={n.icon} />
                <span>{n.label}</span>
                {page === n.id && <i />}
              </button>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="care-card">
            <div className="care-icon">
              <Icon name="shield" size={21} />
            </div>
            <h3>Care starts here.</h3>
            <p>
              Supporting a healthier
              <br />
              student community.
            </p>
            <span>
              IDSC Clinic System <Icon name="activity" size={15} />
            </span>
          </div>
          <button
            className="nav-item logout"
            disabled={busy}
            onClick={() => {
              request("/api/auth/logout/", "POST")
                .then(() => {
                  clearSession();
                  setError("");
                })
                .catch((e) => setError(e.message));
            }}
          >
            <Icon name="logout" />
            <span>Log out</span>
          </button>
          <div className="sidebar-version">
            CLINIC SYSTEM <span>v1.0</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMenuOpen(true)}
            >
              <Icon name="menu" />
            </button>
            <span className="breadcrumb">Workspace</span>
            <Icon name="chevron" size={13} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-right">
            {themeToggle}
            <span className="demo-label">
              <i /> Connected workspace
            </span>
            <div className="topbar-separator" />
            <button className="profile" onClick={() => navigate("settings")}>
              <div className="avatar">CS</div>
              <div>
                <strong>{session?.username}</strong>
                <span>
                  {session?.role === "OWNER"
                    ? "Website owner"
                    : session?.role === "ADMIN"
                      ? "Clinic administrator"
                      : "Clinic staff"}
                </span>
              </div>
              <Icon name="chevron" size={15} />
            </button>
          </div>
        </header>
        <main>
          {busy && <p role="status">Loading clinic data…</p>}
          {inventoryNotices.length > 0 && page !== "medicines" && (
            <div className="notice" role="status">
              <span>{inventoryNotices[0].message}</span>
              <button
                className="button secondary"
                onClick={() => navigate("medicines")}
              >
                View inventory updates
              </button>
            </div>
          )}
          {error && (
            <div className="notice" role="alert">
              {error}
              <button onClick={() => act(async () => {})}>Retry</button>
            </div>
          )}
          {page === "dashboard" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">YOUR CLINIC AT A GLANCE</div>
                  <h1>Dashboard</h1>
                  <p>An overview of your campus health and clinic activity.</p>
                </div>
                <div className="date-chip">
                  <Icon name="calendar" size={17} />
                  {date(new Date().toISOString())}
                </div>
              </div>
              <section className="welcome-banner">
                <div className="banner-copy">
                  <span className="banner-tag">
                    <i /> STUDENT WELLNESS, FIRST
                  </span>
                  <h2>Good care starts with a clear picture.</h2>
                  <p>
                    Keep health records organized and every student’s well-being
                    in focus.
                  </p>
                  <Button
                    variant="secondary"
                    onClick={() => navigate("students")}
                    icon="students"
                  >
                    View students <Icon name="arrow" size={16} />
                  </Button>
                </div>
                <div className="banner-art" aria-hidden="true">
                  <div className="art-orbit orbit-one" />
                  <div className="art-orbit orbit-two" />
                  <div className="art-cross">
                    <span />
                    <span />
                  </div>
                  <div className="art-leaf leaf-one" />
                  <div className="art-leaf leaf-two" />
                  <div className="art-dot dot-one" />
                  <div className="art-dot dot-two" />
                </div>
              </section>
              <div className="stats-grid">
                {[
                  {
                    label: "Total students",
                    value: sampleSummary.total_students,
                    icon: "students",
                    source: "Registrar integration",
                    link: "students",
                  },
                  {
                    label: "Health records",
                    value: sampleSummary.total_health_records,
                    icon: "record",
                    source: "Clinic-managed records",
                    link: "students",
                  },
                  {
                    label: "Total medicine stock",
                    value: sampleSummary.total_medicine_stock,
                    icon: "pill",
                    source: "Units from Inventory",
                    link: "medicines",
                  },
                  {
                    label: "Low-stock medicines",
                    value: sampleSummary.low_stock_medicines,
                    icon: "alert",
                    source: "At or below reorder level",
                    link: "medicines",
                  },
                ].map((s, index) => (
                  <button
                    key={s.label}
                    className={`stat-card ${index === 3 ? "warning-stat" : ""}`}
                    onClick={() => {
                      navigate(s.link);
                      if (index === 3) setFilter("Low stock");
                    }}
                  >
                    <div className="stat-top">
                      <span>{s.label}</span>
                      <div className="stat-icon">
                        <Icon name={s.icon} size={21} />
                      </div>
                    </div>
                    <strong className="stat-value">
                      {s.value.toLocaleString()}
                    </strong>
                    <div className="stat-bottom">
                      <span>{s.source}</span>
                      <Icon name="arrow" size={15} />
                    </div>
                  </button>
                ))}
              </div>
              <div className="dashboard-columns">
                <section className="panel activity-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Recent activity</h2>
                      <p>The latest updates from your clinic.</p>
                    </div>
                    <span className="subtle-chip">Clinic activity</span>
                  </div>
                  <div className="activity-list">
                    {activities.map((a, index) => {
                      const student = students.find(
                        (s) => s.student_id === a.student_id,
                      );
                      return (
                        <div
                          className="activity-row"
                          key={`${a.activity_type}-${a.reference_id}-${index}`}
                        >
                          <div className="activity-icon">
                            <Icon
                              name={
                                a.activity_type === "CONSULTATION"
                                  ? "activity"
                                  : a.activity_type === "HEALTH_STATUS"
                                    ? "shield"
                                    : "record"
                              }
                            />
                          </div>
                          <div className="activity-text">
                            <h3>{activityLabels[a.activity_type]}</h3>
                            <p>
                              {student ? fullname(student) : a.student_id}
                              <span>·</span>
                              {a.student_id}
                            </p>
                            <small>Reference #{a.reference_id}</small>
                          </div>
                          <div className="activity-time">
                            <span>{date(a.occurred_at, true)}</span>
                            <button
                              className="text-link"
                              onClick={() => {
                                if (student) {
                                  openStudent(student);
                                  setTab(
                                    a.activity_type === "CONSULTATION"
                                      ? "Consultations"
                                      : a.activity_type === "HEALTH_STATUS"
                                        ? "Health status"
                                        : "Health record",
                                  );
                                }
                              }}
                            >
                              View student <Icon name="arrow" size={14} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="panel-foot">
                    <Icon name="clock" size={15} />
                    <span>
                      Activity timestamps are shown in Philippine time.
                    </span>
                  </div>
                </section>
                <section className="panel stock-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Stock attention</h2>
                      <p>Medicines that need a closer look.</p>
                    </div>
                    <span className="attention-dot">
                      <Icon name="alert" size={18} />
                    </span>
                  </div>
                  <div className="stock-list">
                    {lowStock.map((m) => (
                      <button
                        className="stock-row"
                        key={m.medicine_id}
                        onClick={() => setMedicine(m)}
                      >
                        <div
                          className={`medicine-icon ${m.quantity_in_stock === 0 ? "muted" : ""}`}
                        >
                          <Icon name="pill" size={19} />
                        </div>
                        <div className="stock-name">
                          <strong>{m.name}</strong>
                          <span>{m.medicine_id}</span>
                        </div>
                        <div className="stock-quantity">
                          <strong>
                            {m.quantity_in_stock} <small>{m.unit}s</small>
                          </strong>
                          <span>
                            {m.quantity_in_stock === 0
                              ? "Out of stock"
                              : "Low stock"}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="stock-panel-note">
                    <Icon name="refresh" size={14} />
                    Read-only data from Inventory
                  </div>
                  <button
                    className="panel-link"
                    onClick={() => navigate("medicines")}
                  >
                    View medicine stock
                    <Icon name="arrow" size={16} />
                  </button>
                </section>
              </div>
              <section className="quick-section">
                <div className="section-title">
                  <h2>Quick access</h2>
                  <span>Your everyday clinic tasks, a little closer.</span>
                </div>
                <div className="quick-grid">
                  {[
                    {
                      icon: "students",
                      title: "Student health records",
                      desc: "Find a student and manage their care.",
                      page: "students",
                    },
                    {
                      icon: "pill",
                      title: "Medicine inventory",
                      desc: "Check availability and stock levels.",
                      page: "medicines",
                    },
                    {
                      icon: "shield",
                      title: "User administration",
                      desc: "Manage clinic staff accounts.",
                      page: "admin",
                    },
                  ]
                    .filter((q) => q.page !== "admin" || admin)
                    .map((q) => (
                      <button
                        className="quick-card"
                        key={q.title}
                        onClick={() => navigate(q.page)}
                      >
                        <div className="quick-icon">
                          <Icon name={q.icon} size={21} />
                        </div>
                        <div>
                          <h3>{q.title}</h3>
                          <p>{q.desc}</p>
                        </div>
                        <Icon name="chevron" size={17} />
                      </button>
                    ))}
                </div>
              </section>
              <div className="sample-note">
                <Icon name="eye" size={14} />
                <span>
                  Connected to the Clinic API. Business data uses the verified
                  mock repository and resets when the backend restarts.
                </span>
              </div>
            </>
          )}

          {page === "registrar" && session?.role === "OWNER" && (
            <MockWorkspace kind="registrar" onRefresh={refreshExternal} />
          )}
          {page === "inventory" && session?.role === "OWNER" && (
            <MockWorkspace kind="inventory" onRefresh={refreshExternal} />
          )}
          {page === "students" && !selected && (
            <GetStudent
              onFound={async (student) => {
                await refreshExternal();
                openStudent(student);
              }}
            />
          )}
          {page === "students" && !selected && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">STUDENT CARE</div>
                  <h1>Students</h1>
                  <p>Find a student to view and manage their clinic records.</p>
                </div>
                <span className="integration-chip">
                  <Icon name="lock" size={14} />
                  Registrar · Read-only
                </span>
              </div>
              <section className="panel">
                <div className="table-toolbar">
                  <Search
                    value={search}
                    onChange={setSearch}
                    placeholder="Search name, student ID, course..."
                  />
                  <div className="filter-control">
                    <span>Course</span>
                    <select
                      aria-label="Filter course"
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                    >
                      <option value="All">All courses</option>
                      <option>BSIT</option>
                      <option>BSCS</option>
                    </select>
                  </div>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Student ID</th>
                        <th>Course</th>
                        <th>Section</th>
                        <th>Status</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {filteredStudents.map((s) => (
                        <tr key={s.student_id}>
                          <td>
                            <button
                              className="student-cell"
                              onClick={() => openStudent(s)}
                            >
                              <div className="avatar student-avatar">
                                {s.first_name[0]}
                                {s.last_name[0]}
                              </div>
                              <strong>{fullname(s)}</strong>
                            </button>
                          </td>
                          <td className="mono">{s.student_id}</td>
                          <td>{s.course}</td>
                          <td>{s.section}</td>
                          <td>
                            <Badge value={s.status} />
                          </td>
                          <td>
                            <button
                              className="text-link"
                              onClick={() => openStudent(s)}
                            >
                              View records
                              <Icon name="arrow" size={15} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!filteredStudents.length && (
                  <Empty detail="Try a different student name, ID, or course." />
                )}
                <div className="table-footer">
                  <span>
                    Showing {filteredStudents.length} of {students.length}{" "}
                    students
                  </span>
                  <span>Page 1 of 1</span>
                </div>
              </section>
              <div className="sample-note">
                <Icon name="shield" size={15} />
                Student identity and profile data are owned by the Registrar
                System.
              </div>
            </>
          )}
          {page === "students" && selected && (
            <>
              <button
                className="back-link"
                onClick={() => {
                  setSelected(null);
                  setSearch("");
                }}
              >
                <span className="back-arrow">
                  <Icon name="arrow" size={16} />
                </span>
                Back to students
              </button>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">STUDENT CARE</div>
                  <h1>Student health record</h1>
                  <p>A complete view of this student’s clinic-managed care.</p>
                </div>
              </div>
              <div className="panel student-profile">
                <div className="avatar large-avatar">
                  {selected.first_name[0]}
                  {selected.last_name[0]}
                </div>
                <div>
                  <h2>{fullname(selected)}</h2>
                  <p>
                    {selected.student_id}
                    <span>·</span>
                    {selected.course}
                    <span>·</span>Section {selected.section}
                  </p>
                </div>
                <Badge value={selected.status} />
                <span className="profile-source">
                  <Icon name="lock" size={14} />
                  Registrar profile
                </span>
              </div>
              <div className="tabs" role="tablist">
                {["Health record", "Consultations", "Health status"].map(
                  (t) => (
                    <button
                      role="tab"
                      aria-selected={tab === t}
                      className={tab === t ? "active" : ""}
                      key={t}
                      onClick={() => {
                        setTab(t);
                        setSearch("");
                      }}
                    >
                      <Icon
                        name={
                          t === "Health record"
                            ? "record"
                            : t === "Consultations"
                              ? "activity"
                              : "shield"
                        }
                        size={18}
                      />
                      {t}
                      <span>
                        {t === "Health record"
                          ? studentRecords.length
                          : t === "Consultations"
                            ? visits.filter(
                                (v) => v.student_id === selected.student_id,
                              ).length
                            : studentStatuses.length}
                      </span>
                    </button>
                  ),
                )}
              </div>
              <section className="panel record-panel">
                <div className="panel-heading">
                  <div>
                    <h2>
                      {tab === "Health record"
                        ? "Health information"
                        : tab === "Consultations"
                          ? "Consultation / clinic visits"
                          : "Health status history"}
                    </h2>
                    <p>
                      {tab === "Health record"
                        ? "Persistent health information and medical history."
                        : tab === "Consultations"
                          ? "Complaints, assessments, and treatment at each visit."
                          : "Clinic-issued health clearances and restrictions."}
                    </p>
                  </div>
                  <Button
                    icon="plus"
                    disabled={selected.status !== "ACTIVE"}
                    onClick={() =>
                      setEditor({
                        kind:
                          tab === "Health record"
                            ? "record"
                            : tab === "Consultations"
                              ? "consultation"
                              : "status",
                      })
                    }
                  >
                    {tab === "Health record"
                      ? "Create record"
                      : tab === "Consultations"
                        ? "New consultation"
                        : "Record status"}
                  </Button>
                </div>
                {selected.status !== "ACTIVE" && (
                  <div className="notice">
                    New clinic records can only be created for active students.
                  </div>
                )}
                {tab === "Health record" &&
                  (studentRecords.length ? (
                    studentRecords.map((r, index) => (
                      <article
                        className="record-article"
                        key={r.health_record_id}
                      >
                        <div className="record-meta">
                          <span>Health record #{index + 1}</span>
                          <div className="row-actions">
                            <button
                              className="icon-button"
                              aria-label="Edit health record"
                              onClick={() =>
                                setEditor({ kind: "record", existing: r })
                              }
                            >
                              <Icon name="edit" size={17} />
                            </button>
                            {admin && (
                              <button
                                className="icon-button danger-icon"
                                aria-label="Delete health record"
                                onClick={() =>
                                  deleteRecord("record", r.health_record_id)
                                }
                              >
                                <Icon name="trash" size={17} />
                              </button>
                            )}
                          </div>
                        </div>
                        <div className="vitals-grid">
                          <div>
                            <span>Blood type</span>
                            <strong>{r.blood_type ?? "Not recorded"}</strong>
                          </div>
                          <div>
                            <span>Height</span>
                            <strong>
                              {r.height_cm ?? "—"} <small>cm</small>
                            </strong>
                          </div>
                          <div>
                            <span>Weight</span>
                            <strong>
                              {r.weight_kg ?? "—"} <small>kg</small>
                            </strong>
                          </div>
                        </div>
                        <dl className="record-details">
                          <div>
                            <dt>Allergies</dt>
                            <dd>{r.allergies || "Not recorded"}</dd>
                          </div>
                          <div>
                            <dt>Medical history</dt>
                            <dd>{r.medical_history || "Not recorded"}</dd>
                          </div>
                          <div>
                            <dt>Current medications</dt>
                            <dd>{r.current_medications || "Not recorded"}</dd>
                          </div>
                        </dl>
                        <div className="record-dates">
                          <span>Created {date(r.created_at)}</span>
                          <span>Updated {date(r.updated_at)}</span>
                        </div>
                      </article>
                    ))
                  ) : (
                    <Empty
                      text="No health records yet"
                      detail="Create a health record for this student to get started."
                    />
                  ))}
                {tab === "Consultations" && (
                  <>
                    <div className="record-search">
                      <Search
                        value={search}
                        onChange={setSearch}
                        placeholder="Search complaints, assessments, or notes..."
                      />
                    </div>
                    {studentVisits.length ? (
                      studentVisits.map((v) => (
                        <article
                          className="record-article"
                          key={v.consultation_id}
                        >
                          <div className="record-meta">
                            <div>
                              <Badge value="CONSULTATION" />
                              <span className="visit-date">
                                {date(v.consulted_at, true)} · #
                                {visits
                                  .filter(
                                    (item) =>
                                      item.student_id === selected.student_id,
                                  )
                                  .findIndex(
                                    (item) =>
                                      item.consultation_id ===
                                      v.consultation_id,
                                  ) + 1}
                              </span>
                            </div>
                            <div className="row-actions">
                              <button
                                className="icon-button"
                                aria-label="Edit consultation"
                                onClick={() =>
                                  setEditor({
                                    kind: "consultation",
                                    existing: v,
                                  })
                                }
                              >
                                <Icon name="edit" size={17} />
                              </button>
                              {admin && (
                                <button
                                  className="icon-button danger-icon"
                                  aria-label="Delete consultation"
                                  onClick={() =>
                                    deleteRecord(
                                      "consultation",
                                      v.consultation_id,
                                    )
                                  }
                                >
                                  <Icon name="trash" size={17} />
                                </button>
                              )}
                            </div>
                          </div>
                          <h3 className="complaint">{v.chief_complaint}</h3>
                          <dl className="record-details">
                            <div>
                              <dt>Assessment</dt>
                              <dd>{v.assessment || "Not recorded"}</dd>
                            </div>
                            <div>
                              <dt>Treatment</dt>
                              <dd>{v.treatment || "Not recorded"}</dd>
                            </div>
                            <div>
                              <dt>Notes</dt>
                              <dd>{v.notes || "Not recorded"}</dd>
                            </div>
                          </dl>
                        </article>
                      ))
                    ) : (
                      <Empty
                        text="No consultations found"
                        detail={
                          search
                            ? "Try another complaint or assessment."
                            : "Record this student’s first clinic visit."
                        }
                      />
                    )}
                  </>
                )}
                {tab === "Health status" &&
                  (studentStatuses.length ? (
                    studentStatuses.map((s) => (
                      <article className="record-article" key={s.status_id}>
                        <div className="record-meta">
                          <Badge value={s.status} />
                          <div className="row-actions">
                            <button
                              className="icon-button"
                              aria-label="Edit health status"
                              onClick={() =>
                                setEditor({ kind: "status", existing: s })
                              }
                            >
                              <Icon name="edit" size={17} />
                            </button>
                            {admin && (
                              <button
                                className="icon-button danger-icon"
                                aria-label="Delete health status"
                                onClick={() =>
                                  deleteRecord("status", s.status_id)
                                }
                              >
                                <Icon name="trash" size={17} />
                              </button>
                            )}
                          </div>
                        </div>
                        <p className="status-remarks">
                          {s.remarks || "No remarks"}
                        </p>
                        <div className="record-dates">
                          <span>Status #{s.status_id}</span>
                          <span>Effective {date(s.effective_at, true)}</span>
                        </div>
                      </article>
                    ))
                  ) : (
                    <Empty
                      text="No health status available"
                      detail="Record a clearance, restriction, or observation status."
                    />
                  ))}
              </section>
              {tab === "Health status" && (
                <div className="notice integration-notice">
                  <Icon name="shield" />
                  <div>
                    <strong>Faculty & Student Portal integrations</strong>
                    <p>
                      The contract permits read-only access to the latest
                      status, remarks, and effective date only. Full health
                      records and consultations are not shared.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}

          {page === "medicines" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">MEDICINE INVENTORY</div>
                  <h1>Medicine stock</h1>
                  <p>
                    Check medicine availability and monitor low-stock items.
                  </p>
                </div>
                <Button
                  variant="secondary"
                  icon="refresh"
                  onClick={() => act(async () => {})}
                >
                  Request stock information
                </Button>
              </div>
              <RestockPanel
                medicines={medicines}
                requests={restockRequests}
                notices={inventoryNotices}
                onRefresh={refreshExternal}
              />
              <div className="medicine-summary">
                <div>
                  <div className="stat-icon">
                    <Icon name="pill" />
                  </div>
                  <span>
                    Total stock
                    <strong>
                      {medicines.reduce((n, m) => n + m.quantity_in_stock, 0)}{" "}
                      <small>tablets</small>
                    </strong>
                  </span>
                </div>
                <div>
                  <div className="stat-icon">
                    <Icon name="check" />
                  </div>
                  <span>
                    Available medicines
                    <strong>
                      {medicines.filter((m) => m.quantity_in_stock > 0).length}
                    </strong>
                  </span>
                </div>
                <div>
                  <div className="stat-icon amber-icon">
                    <Icon name="alert" />
                  </div>
                  <span>
                    Low-stock medicines<strong>{lowStock.length}</strong>
                  </span>
                </div>
              </div>
              <section className="panel">
                <div className="table-toolbar">
                  <Search
                    value={search}
                    onChange={setSearch}
                    placeholder="Search medicine name or ID..."
                  />
                  <div className="segmented">
                    {["All", "Available", "Low stock"].map((f) => (
                      <button
                        key={f}
                        className={filter === f ? "active" : ""}
                        onClick={() => setFilter(f)}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Medicine</th>
                        <th>Medicine ID</th>
                        <th>Stock quantity</th>
                        <th>Reorder level</th>
                        <th>Availability</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {filteredMedicines.map((m) => (
                        <tr key={m.medicine_id}>
                          <td>
                            <button
                              className="student-cell"
                              onClick={() => setMedicine(m)}
                            >
                              <div className="medicine-icon">
                                <Icon name="pill" size={20} />
                              </div>
                              <div className="table-name">
                                <strong>{m.name}</strong>
                                <span>{m.generic_name}</span>
                              </div>
                            </button>
                          </td>
                          <td className="mono">{m.medicine_id}</td>
                          <td>
                            <strong>{m.quantity_in_stock}</strong>{" "}
                            <span className="muted-text">{m.unit}s</span>
                          </td>
                          <td>{m.reorder_level}</td>
                          <td>
                            <Badge
                              value={
                                m.quantity_in_stock === 0
                                  ? "Out of stock"
                                  : m.is_low_stock
                                    ? "Low stock"
                                    : "Available"
                              }
                            />
                          </td>
                          <td>
                            <button
                              className="icon-button"
                              aria-label={`View ${m.name}`}
                              onClick={() => setMedicine(m)}
                            >
                              <Icon name="chevron" size={18} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!filteredMedicines.length && (
                  <Empty
                    text="No medicines found"
                    detail="Try a different medicine name or filter."
                  />
                )}
                <div className="table-footer">
                  <span>
                    Showing {filteredMedicines.length} of {medicines.length}{" "}
                    medicines
                  </span>
                  <span>Inventory · Read-only</span>
                </div>
              </section>
              <div className="sample-note">
                <Icon name="lock" size={15} />
                Medicine catalog and stock belong to Inventory. Low stock means
                quantity is at or below the reorder level.
              </div>
            </>
          )}
          {page === "settings" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">YOUR ACCOUNT</div>
                  <h1>Settings</h1>
                  <p>Account information and sign-in preferences.</p>
                </div>
              </div>
              <div className="settings-layout">
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Account information</h2>
                      <p>Current authenticated account.</p>
                    </div>
                    <Icon name="students" />
                  </div>
                  <dl className="record-details settings-details">
                    <div>
                      <dt>User ID</dt>
                      <dd>{session?.id}</dd>
                    </div>
                    <div>
                      <dt>Username</dt>
                      <dd>{session?.username}</dd>
                    </div>
                    <div>
                      <dt>Email</dt>
                      <dd>{session?.email}</dd>
                    </div>
                    <div>
                      <dt>Account access</dt>
                      <dd>
                        {session?.role === "OWNER"
                          ? "Website owner"
                          : session?.role === "ADMIN"
                            ? "Clinic administrator"
                            : "Clinic staff"}
                      </dd>
                    </div>
                  </dl>
                  <div className="panel-foot">Authenticated Django session</div>
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Sign-in & security</h2>
                      <p>Manage your account credentials.</p>
                    </div>
                    <Icon name="lock" />
                  </div>
                  <div className="settings-option">
                    <div>
                      <h3>Change username</h3>
                      <p>Update your clinic sign-in username.</p>
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => setUsernameOpen(true)}
                    >
                      Change username
                    </Button>
                  </div>
                  <div className="settings-option">
                    <div>
                      <h3>Change password</h3>
                      <p>Update your account password.</p>
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => setPasswordOpen(true)}
                    >
                      Change password
                    </Button>
                  </div>
                  <div className="notice">
                    Username and password changes require your current password.
                  </div>
                </section>
              </div>
            </>
          )}
          {page === "admin" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">CLINIC MANAGEMENT</div>
                  <h1>Administration</h1>
                  <p>
                    {session?.role === "OWNER"
                      ? "Manage administrator and staff accounts."
                      : "Manage staff profiles and account access."}
                  </p>
                </div>
                <div className="account-create-actions">
                  {session?.role === "OWNER" && (
                    <Button
                      variant="secondary"
                      icon="shield"
                      disabled={busy || adminLimitReached}
                      title={
                        adminLimitReached
                          ? "Delete an administrator before adding a new one."
                          : undefined
                      }
                      onClick={() => setEditor({ kind: "admin" })}
                    >
                      Add administrator
                    </Button>
                  )}
                  <Button
                    icon="plus"
                    onClick={() => setEditor({ kind: "user" })}
                  >
                    Add staff account
                  </Button>
                </div>
              </div>
              <div className="notice admin-notice">
                <Icon name="shield" size={18} />
                <span>
                  {session?.role === "OWNER"
                    ? "Owner access: manage administrators and staff."
                    : "Administrator access: manage staff accounts."}
                </span>
              </div>
              {session?.role === "OWNER" && (
                <section className="panel admin-accounts-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Administrators ({admins.length}/5)</h2>
                      {adminLimitReached && (
                        <p role="status">
                          Administrator limit reached. Delete an administrator
                          before adding a new one. Inactive accounts still
                          count.
                        </p>
                      )}
                      <p>
                        Only the website owner can create and manage
                        administrator accounts. Administrators can manage staff
                        and use clinic features.
                      </p>
                      <p>
                        Owner accounts are separate and cannot be deleted or
                        deactivated here. Change your own username and password
                        in Settings.
                      </p>
                    </div>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Username</th>
                          <th>Name</th>
                          <th>Email</th>
                          <th>Access</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {admins.map((account) => (
                          <tr key={account.user_id}>
                            <td>
                              {account.username}
                              {account.user_id === session?.id ? " (you)" : ""}
                            </td>
                            <td>
                              {`${account.first_name} ${account.last_name}`.trim() ||
                                "—"}
                            </td>
                            <td>{account.email || "—"}</td>
                            <td>Clinic administrator</td>
                            <td>
                              <Badge
                                value={
                                  account.is_active ? "ACTIVE" : "INACTIVE"
                                }
                              />
                            </td>
                            <td>
                              <div className="row-actions">
                                <button
                                  className="text-link"
                                  disabled={busy || !account.can_manage}
                                  onClick={() =>
                                    setEditor({
                                      kind: "admin",
                                      existing: account,
                                    })
                                  }
                                >
                                  Edit
                                </button>
                                <button
                                  className={`text-link ${account.is_active ? "danger-link" : ""}`}
                                  disabled={busy || !account.can_manage}
                                  title={
                                    account.management_restriction || undefined
                                  }
                                  onClick={() =>
                                    confirmAccountAction(
                                      "admins",
                                      account,
                                      account.is_active
                                        ? "deactivate"
                                        : "activate",
                                    )
                                  }
                                >
                                  {account.is_active
                                    ? "Deactivate"
                                    : "Activate"}
                                </button>
                                <button
                                  className="text-link danger-link"
                                  disabled={busy || !account.can_manage}
                                  title={
                                    account.management_restriction || undefined
                                  }
                                  onClick={() =>
                                    confirmAccountAction(
                                      "admins",
                                      account,
                                      "delete",
                                    )
                                  }
                                >
                                  Delete
                                </button>
                              </div>
                              {account.management_restriction && (
                                <small className="account-restriction">
                                  {account.management_restriction}
                                </small>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
              <section className="panel">
                <div className="table-toolbar">
                  <Search
                    value={search}
                    onChange={(value) => {
                      setSearch(value);
                      setStaffPage(1);
                    }}
                    placeholder="Search staff name, username, or email..."
                  />
                  <span className="muted-text">
                    {users.length} staff{" "}
                    {users.length === 1 ? "account" : "accounts"}
                  </span>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Staff member</th>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleStaff.map((u) => (
                        <tr key={u.user_id}>
                          <td>
                            <div className="student-cell">
                              <div className="avatar student-avatar">
                                {u.first_name[0] ?? "C"}
                                {u.last_name[0] ?? "S"}
                              </div>
                              <div className="table-name">
                                <strong>
                                  {u.first_name} {u.last_name}
                                </strong>
                                <span>{u.email || "No email provided"}</span>
                              </div>
                            </div>
                          </td>
                          <td>{u.username}</td>
                          <td>{u.role ?? "Not assigned"}</td>
                          <td>
                            <Badge
                              value={u.is_active ? "ACTIVE" : "INACTIVE"}
                            />
                          </td>
                          <td>
                            <div className="row-actions">
                              <button
                                className="text-link"
                                onClick={() =>
                                  setEditor({ kind: "user", existing: u })
                                }
                              >
                                <Icon name="edit" size={15} />
                                Edit
                              </button>
                              <button
                                className={`text-link ${u.is_active ? "danger-link" : ""}`}
                                disabled={busy || u.role === "ADMIN"}
                                title={
                                  u.role === "ADMIN"
                                    ? "Manage this account in the administrators table."
                                    : undefined
                                }
                                onClick={() =>
                                  confirmAccountAction(
                                    "users",
                                    u,
                                    u.is_active ? "deactivate" : "activate",
                                  )
                                }
                              >
                                {u.is_active ? "Deactivate" : "Activate"}
                              </button>
                              <button
                                className="text-link danger-link"
                                disabled={busy || u.role === "ADMIN"}
                                title={
                                  u.role === "ADMIN"
                                    ? "Manage this account in the administrators table."
                                    : undefined
                                }
                                onClick={() =>
                                  confirmAccountAction("users", u, "delete")
                                }
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!filteredUsers.length && (
                  <Empty
                    text="No staff accounts found"
                    detail="Try a different staff name, username, or email."
                  />
                )}
                <div className="table-footer">
                  <span>
                    {filteredUsers.length
                      ? `${(currentStaffPage - 1) * 10 + 1}–${Math.min(currentStaffPage * 10, filteredUsers.length)} of `
                      : ""}
                    {filteredUsers.length}{" "}
                    {filteredUsers.length === 1 ? "account" : "accounts"}
                  </span>
                  <nav
                    className="staff-pagination"
                    aria-label="Staff account pages"
                  >
                    <Button
                      variant="secondary"
                      disabled={busy || currentStaffPage === 1}
                      onClick={() => setStaffPage(currentStaffPage - 1)}
                    >
                      Previous
                    </Button>
                    <span aria-live="polite">
                      Page {currentStaffPage} of {staffTotalPages}
                    </span>
                    <Button
                      variant="secondary"
                      disabled={busy || currentStaffPage === staffTotalPages}
                      onClick={() => setStaffPage(currentStaffPage + 1)}
                    >
                      Next
                    </Button>
                  </nav>
                </div>
              </section>
              <div className="sample-note">
                <Icon name="lock" size={15} />
                Deactivation can be reversed. Deleting an account is permanent
                and requires your current password. Clinic medical records
                remain.
              </div>
            </>
          )}
          {page === "medicines" && (
            <section className="panel" style={{ padding: 24 }}>
              <h2>Dispense medicine</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.currentTarget;
                  const data = Object.fromEntries(new FormData(form));
                  data.quantity = Number(data.quantity);
                  if (
                    await act(() =>
                      request("/api/v1/medicine-dispensations/", "POST", data),
                    )
                  )
                    form.reset();
                }}
              >
                <label className="field">
                  Student
                  <select name="student_id" required>
                    {students
                      .filter((s) => s.status === "ACTIVE")
                      .map((s) => (
                        <option key={s.student_id} value={s.student_id}>
                          {fullname(s)} · {s.student_id}
                        </option>
                      ))}
                  </select>
                </label>
                <label className="field">
                  Medicine
                  <select name="medicine_id" required>
                    {medicines
                      .filter((m) => m.status === "ACTIVE")
                      .map((m) => (
                        <option key={m.medicine_id} value={m.medicine_id}>
                          {m.name} · {m.quantity_in_stock} available
                        </option>
                      ))}
                  </select>
                </label>
                <Field
                  label="Quantity"
                  name="quantity"
                  type="number"
                  min={1}
                  required
                />
                <Field label="Reason" name="reason" required />
                <Button type="submit" disabled={busy}>
                  Dispense
                </Button>
              </form>
              <h2>Dispensing history</h2>
              {dispensations.map((d) => (
                <div key={d.dispensation_id} className="settings-option">
                  <span>
                    #{d.dispensation_id} · {d.student_id} · {d.medicine_id} ·{" "}
                    {d.quantity} · {d.status}
                  </span>
                  {admin && (
                    <Button
                      variant="danger"
                      disabled={busy}
                      onClick={() => {
                        setError("");
                        setConfirmation({
                          title: "Delete dispensing history?",
                          description:
                            "Permanently delete this clinic history entry? Medicine stock and Inventory transactions will stay unchanged. Use Roll back first if you need to return stock.",
                          action: () =>
                            act(() =>
                              request(
                                `/api/v1/medicine-dispensations/${d.dispensation_id}/`,
                                "DELETE",
                              ),
                            ),
                        });
                      }}
                    >
                      Delete dispensing history
                    </Button>
                  )}
                  {d.status === "COMPLETED" && (
                    <Button
                      disabled={busy}
                      variant="secondary"
                      onClick={() =>
                        setConfirmation({
                          title:
                            "Roll back dispensation #" +
                            d.dispensation_id +
                            "?",
                          action: () =>
                            act(() =>
                              request(
                                "/api/v1/medicine-dispensations/" +
                                  d.dispensation_id +
                                  "/rollback/",
                                "POST",
                              ),
                            ),
                        })
                      }
                    >
                      Roll back
                    </Button>
                  )}
                </div>
              ))}
            </section>
          )}
          {page === "dashboard" && (
            <section className="panel" style={{ padding: 24 }}>
              <h2>Clinic reports</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const data = new FormData(e.currentTarget);
                  const params = new URLSearchParams();
                  for (const key of ["date_from", "date_to"])
                    if (data.get(key)) params.set(key, data.get(key));
                  setError("");
                  try {
                    setReport(
                      await request(
                        "/api/v1/reports/" + data.get("report") + "/?" + params,
                      ),
                    );
                  } catch (e) {
                    setError(e.message);
                  }
                }}
              >
                <label className="field">
                  Report
                  <select name="report">
                    {[
                      "clinic-visits",
                      "health-records",
                      "medicine-inventory",
                      "medicine-dispensations",
                    ].map((r) => (
                      <option key={r}>{r}</option>
                    ))}
                  </select>
                </label>
                <Field label="From date" type="date" name="date_from" />
                <Field label="To date" type="date" name="date_to" />
                <Button type="submit">View report</Button>
              </form>
              {report && (
                <div className="table-scroll">
                  <div className="report-summary">
                    {Object.entries(report)
                      .filter(([key]) => key !== "results")
                      .map(([key, value]) => (
                        <p key={key}>
                          <strong>{key.replaceAll("_", " ")}: </strong>
                          {String(value)}
                        </p>
                      ))}
                    {report.results?.length ? (
                      <table>
                        <thead>
                          <tr>
                            {Object.keys(report.results[0]).map((key) => (
                              <th key={key}>{key.replaceAll("_", " ")}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {report.results.map((row, index) => (
                            <tr key={index}>
                              {Object.values(row).map((value, index) => (
                                <td key={index}>
                                  {value == null ? "�" : String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p>No records for this report.</p>
                    )}
                  </div>
                </div>
              )}
            </section>
          )}
          <footer className="app-footer">
            <span>IDSC Clinic System</span>
            <span>Thoughtful care. Connected information.</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Icon name="check" size={18} />
          {toast}
          <button
            className="icon-button"
            onClick={() => setToast("")}
            aria-label="Dismiss message"
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
      {usernameOpen && (
        <UsernameChangeDialog
          username={session?.username}
          onClose={() => setUsernameOpen(false)}
          onSuccess={(user) => {
            setSession(user);
            setUsernameOpen(false);
            setAdmins((values) =>
              values.map((account) =>
                account.user_id === user.id
                  ? { ...account, username: user.username }
                  : account,
              ),
            );
            setToast(
              "Username changed. Use your new username the next time you sign in.",
            );
          }}
          onExpired={() => {
            clearSession();
            setLoginError("Your session has expired. Please sign in again.");
          }}
        />
      )}
      {passwordOpen && (
        <PasswordChangeDialog
          onClose={() => setPasswordOpen(false)}
          onSuccess={() => {
            setPasswordOpen(false);
            setToast(
              "Password changed. Your other sessions have been signed out.",
            );
          }}
          onExpired={() => {
            clearSession();
            setLoginError("Your session has expired. Please sign in again.");
          }}
        />
      )}
      {editor && (
        <Modal
          title={`${editor.existing ? "Edit" : "Create"} ${
            editor.kind === "record"
              ? "health record"
              : editor.kind === "status"
                ? "health status"
                : ["user", "admin"].includes(editor.kind)
                  ? editor.kind === "admin"
                    ? "administrator account"
                    : "staff account"
                  : "consultation"
          }`}
          onClose={() => setEditor(null)}
        >
          <form onSubmit={saveEditor}>
            {error && (
              <div className="notice" role="alert">
                {error}
              </div>
            )}
            <div className="modal-content">
              <div className="notice compact">
                Changes are submitted to the Clinic API.
              </div>
              {!["user", "admin"].includes(editor.kind) && (
                <div className="editor-student">
                  <Icon name="students" size={18} />
                  <strong>{selected && fullname(selected)}</strong>
                  <span>{selected?.student_id}</span>
                </div>
              )}
              {editor.kind === "record" &&
                (() => {
                  const r = editor.existing;
                  return (
                    <>
                      <Field
                        label="Blood type"
                        name="blood_type"
                        value={r?.blood_type ?? "Unknown"}
                        options={[
                          "A+",
                          "A-",
                          "B+",
                          "B-",
                          "AB+",
                          "AB-",
                          "O+",
                          "O-",
                          "Unknown",
                        ]}
                      />
                      <div className="form-grid">
                        <Field
                          label="Height (cm)"
                          name="height_cm"
                          type="number"
                          value={r?.height_cm}
                          min={0.01}
                          max={300}
                        />
                        <Field
                          label="Weight (kg)"
                          name="weight_kg"
                          type="number"
                          value={r?.weight_kg}
                          min={0.01}
                          max={500}
                        />
                      </div>
                      <Field
                        label="Allergies"
                        name="allergies"
                        value={r?.allergies}
                        multiline
                      />
                      <Field
                        label="Medical history"
                        name="medical_history"
                        value={r?.medical_history}
                        multiline
                      />
                      <Field
                        label="Current medications"
                        name="current_medications"
                        value={r?.current_medications}
                        multiline
                      />
                    </>
                  );
                })()}
              {editor.kind === "consultation" &&
                (() => {
                  const v = editor.existing;
                  return (
                    <>
                      <Field
                        label="Chief complaint"
                        name="chief_complaint"
                        value={v?.chief_complaint}
                        required
                        multiline
                      />
                      <Field
                        label="Assessment"
                        name="assessment"
                        value={v?.assessment}
                        multiline
                      />
                      <Field
                        label="Treatment"
                        name="treatment"
                        value={v?.treatment}
                        multiline
                      />
                      <Field
                        label="Notes"
                        name="notes"
                        value={v?.notes}
                        multiline
                      />
                    </>
                  );
                })()}
              {editor.kind === "status" &&
                (() => {
                  const s = editor.existing;
                  return (
                    <>
                      <Field
                        label="Status"
                        name="status"
                        value={s?.status}
                        options={["CLEARED", "RESTRICTED", "UNDER_OBSERVATION"]}
                        required
                      />
                      <Field
                        label="Remarks"
                        name="remarks"
                        value={s?.remarks}
                        multiline
                      />
                    </>
                  );
                })()}
              {["user", "admin"].includes(editor.kind) &&
                (() => {
                  const u = editor.existing;
                  return (
                    <>
                      <Field
                        label="Username"
                        name="username"
                        value={u?.username}
                        required
                      />
                      <div className="form-grid">
                        <Field
                          label="First name"
                          name="first_name"
                          value={u?.first_name}
                        />
                        <Field
                          label="Last name"
                          name="last_name"
                          value={u?.last_name}
                        />
                      </div>
                      <Field
                        label="Email"
                        name="email"
                        type="email"
                        value={u?.email}
                      />
                      {!u && (
                        <>
                          <Field
                            label="Temporary password"
                            name="password"
                            type="password"
                            autoComplete="new-password"
                            required
                          />
                          <small className="muted-text">
                            Choose a strong password for the new account.
                          </small>
                          {editor.kind === "admin" && (
                            <>
                              <Field
                                label="Confirm administrator password"
                                name="confirm_password"
                                type="password"
                                autoComplete="new-password"
                                required
                              />
                              <div className="notice compact">
                                This administrator can manage staff and use all
                                clinic features. Only the owner manages
                                administrators. Choose a strong password and
                                enter your own current password to authorize
                                creation.
                              </div>
                              <Field
                                label="Your current password"
                                name="current_password"
                                type="password"
                                autoComplete="current-password"
                                required
                              />
                            </>
                          )}
                        </>
                      )}
                    </>
                  );
                })()}
            </div>
            <div className="modal-actions">
              <Button variant="secondary" onClick={() => setEditor(null)}>
                Cancel
              </Button>
              <Button type="submit" icon="check" disabled={busy}>
                {editor.existing ? "Save changes" : "Create"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
      {confirmation && (
        <Modal
          title={confirmation.title}
          onClose={() => {
            if (!busy) setConfirmation(null);
          }}
        >
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              if (busy) return;
              const password = new FormData(event.currentTarget).get(
                "current_password",
              );
              const succeeded = await confirmation.action(password);
              if (succeeded !== false) setConfirmation(null);
            }}
            aria-busy={busy}
          >
            <div className="modal-content">
              {error && (
                <div className="notice" role="alert">
                  {error}
                </div>
              )}
              <p>
                {confirmation.description ||
                  "Confirm this change to the clinic data."}
                {!confirmation.description &&
                confirmation.title.startsWith("Delete")
                  ? " This action cannot be undone."
                  : ""}
              </p>
              {confirmation.requiresPassword && (
                <div className="confirmation-password">
                  <Field
                    label="Your current password"
                    name="current_password"
                    type="password"
                    autoComplete="current-password"
                    required
                  />
                </div>
              )}
            </div>
            <div className="modal-actions">
              <Button
                variant="secondary"
                onClick={() => setConfirmation(null)}
                disabled={busy}
              >
                Cancel
              </Button>
              <Button variant="danger" disabled={busy} type="submit">
                {busy ? "Working…" : "Confirm"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
      {medicine && (
        <Modal title={medicine.name} onClose={() => setMedicine(null)}>
          <div className="modal-content">
            <span className="integration-chip">
              <Icon name="lock" size={14} />
              Inventory · Read-only
            </span>
            <dl className="record-details medicine-details">
              <div>
                <dt>Medicine ID</dt>
                <dd>{medicine.medicine_id}</dd>
              </div>
              <div>
                <dt>Generic name</dt>
                <dd>{medicine.generic_name}</dd>
              </div>
              <div>
                <dt>Unit</dt>
                <dd>{medicine.unit}</dd>
              </div>
              <div>
                <dt>Quantity in stock</dt>
                <dd>{medicine.quantity_in_stock}</dd>
              </div>
              <div>
                <dt>Reorder level</dt>
                <dd>{medicine.reorder_level}</dd>
              </div>
              <div>
                <dt>Low stock</dt>
                <dd>{String(medicine.is_low_stock)}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <Badge value={medicine.status} />
                </dd>
              </div>
            </dl>
          </div>
          <div className="modal-actions">
            <Button variant="secondary" onClick={() => setMedicine(null)}>
              Close
            </Button>
          </div>
        </Modal>
      )}
      {info && (
        <Modal title="Inventory integration" onClose={() => setInfo("")}>
          <div className="modal-content">
            <p>{info}</p>
          </div>
          <div className="modal-actions">
            <Button variant="secondary" onClick={() => setInfo("")}>
              Close
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
