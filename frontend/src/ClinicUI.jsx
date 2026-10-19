import { useEffect, useEffectEvent, useRef } from "react";
import idscLogo from "./assets/idsc-logo.png";
const paths = {
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  students: (
    <>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      <circle cx="9" cy="7" r="4" />
    </>
  ),
  record: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Zm0 0v6h6M8 13h8M8 17h5" />
    </>
  ),
  pill: (
    <>
      <path d="m9 15 6-6M4.5 19.5a5 5 0 0 1 0-7l8-8a5 5 0 0 1 7 7l-8 8a5 5 0 0 1-7 0Z" />
    </>
  ),
  settings: (
    <>
      <path d="m9 3-1 3-3 1-2 3 2 2-1 3 2 3 3-1 2 3h3l1-3 3-1 2-3-2-2 1-3-2-3-3 1-2-3Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  shield: (
    <>
      <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z" />
      <path d="m8 12 3 3 5-6" />
    </>
  ),
  logout: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5M21 12H9" />
    </>
  ),
  chevron: <path d="m9 5 7 7-7 7" />,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  check: <path d="m5 12 4 4L19 6" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M16 3v4M8 3v4M3 11h18" />
    </>
  ),
  activity: <path d="M2 12h5l3-8 4 16 3-8h5" />,
  alert: (
    <>
      <path d="m10.3 4-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0ZM12 9v4m0 4h.01" />
    </>
  ),
  edit: (
    <>
      <path d="m16 3 5 5-12 12-6 1 1-6Zm-2 2 5 5" />
    </>
  ),
  trash: (
    <>
      <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7" />
    </>
  ),
  refresh: (
    <>
      <path d="M20 7v5h-5M4 17v-5h5M5 8a8 8 0 0 1 13-3l2 3M4 16l2 3a8 8 0 0 0 13-3" />
    </>
  ),
  lock: (
    <>
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3" />
    </>
  ),
  eye: (
    <>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  menu: <path d="M4 6h16M4 12h16M4 18h16" />,
};
export function Icon({ name, size = 20 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
export function Logo() {
  return (
    <div className="brand">
      <img
        className="brand-symbol"
        src={idscLogo}
        alt="Infotech Development Systems Colleges logo"
      />
      <div>
        <strong>IDSC Clinic</strong>
        <small>HEALTH MANAGEMENT</small>
      </div>
    </div>
  );
}
export function Badge({ value }) {
  const tone = ["ACTIVE", "CLEARED", "Available", "COMPLETED"].includes(value)
    ? "green"
    : ["Low stock", "RESTRICTED", "UNDER_OBSERVATION"].includes(value)
      ? "amber"
      : "gray";
  return (
    <span className={`badge ${tone}`}>
      <i />
      {value
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/^./, (x) => x.toUpperCase())}
    </span>
  );
}
export function Button({
  children,
  onClick,
  variant = "primary",
  icon,
  type = "button",
  disabled = false,
}) {
  return (
    <button
      type={type}
      className={`button ${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <Icon name={icon} size={17} />}
      {children}
    </button>
  );
}
export function Search({ value, onChange, placeholder }) {
  return (
    <div className="search">
      <Icon name="search" size={18} />
      <input
        aria-label={placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {value && (
        <button aria-label="Clear search" onClick={() => onChange("")}>
          <Icon name="close" size={15} />
        </button>
      )}
    </div>
  );
}
export function Empty({
  text = "No records found",
  detail = "Try another search or add a new record.",
}) {
  return (
    <div className="empty">
      <Icon name="record" size={30} />
      <h3>{text}</h3>
      <p>{detail}</p>
    </div>
  );
}
export function Modal({ title, children, onClose }) {
  const ref = useRef(null);
  const closeFromKeyboard = useEffectEvent(() => onClose());
  useEffect(() => {
    const previous = document.activeElement;
    const panel = ref.current;
    const firstField = panel?.querySelector(
      'input:not([type="hidden"]):not(:disabled), select:not(:disabled), textarea:not(:disabled)',
    );
    (firstField ?? panel?.querySelector("button:not(:disabled)"))?.focus();
    function key(e) {
      if (e.key === "Escape") closeFromKeyboard();
      if (e.key === "Tab" && panel) {
        const items = Array.from(
          panel.querySelectorAll(
            "button:not(:disabled), input:not(:disabled):not([type='hidden']), select:not(:disabled), textarea:not(:disabled), [tabindex='0']",
          ),
        );
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-heading">
          <h2>{title}</h2>
          <button
            className="icon-button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <Icon name="close" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
export function Field({
  label,
  name,
  value,
  type = "text",
  required = false,
  options,
  multiline = false,
  min,
  max,
  autoComplete,
}) {
  return (
    <label className="field">
      <span>
        {label}
        {required && <em> *</em>}
      </span>
      {options ? (
        <select name={name} defaultValue={value ?? options[0]}>
          {options.map((x) => (
            <option key={x} value={x}>
              {x.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      ) : multiline ? (
        <textarea
          name={name}
          defaultValue={value ?? ""}
          rows={3}
          required={required}
        />
      ) : (
        <input
          name={name}
          type={type}
          autoComplete={autoComplete}
          defaultValue={value ?? ""}
          required={required}
          min={min}
          max={max}
          step={type === "number" ? "0.01" : undefined}
          maxLength={
            name === "email"
              ? 254
              : name === "username" ||
                  name === "first_name" ||
                  name === "last_name"
                ? 150
                : undefined
          }
        />
      )}
    </label>
  );
}
