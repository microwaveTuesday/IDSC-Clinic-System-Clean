import { useState } from "react";
import { request } from "./api";

export default function OwnerRegistration({ onComplete, onAlreadyRegistered }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});
  async function submit(event) {
    event.preventDefault();
    if (pending) return;
    const data = Object.fromEntries(new FormData(event.currentTarget));
    setError("");
    setErrors({});
    if (data.password !== data.confirm_password) {
      setErrors({ confirm_password: ["The passwords do not match."] });
      return;
    }
    setPending(true);
    try {
      const result = await request("/api/auth/owner/register/", "POST", data);
      await onComplete(result.user);
    } catch (e) {
      if (e.status === 409) {
        onAlreadyRegistered();
      } else {
        setError(e.message);
        setErrors(e.body?.errors || {});
      }
    } finally {
      setPending(false);
    }
  }
  return (
    <form
      className="login-form owner-registration"
      onSubmit={submit}
      aria-busy={pending}
    >
      <span className="eyebrow">FIRST-TIME SETUP</span>
      <h2>Register the system Owner</h2>
      <p>
        Create the single Owner account for this installation. The Owner manages
        Admin and Staff accounts.
      </p>
      <fieldset disabled={pending}>
        {[
          ["Username", "username", "text", true, "username"],
          ["First name", "first_name", "text", false, "given-name"],
          ["Last name", "last_name", "text", false, "family-name"],
          ["Email", "email", "email", false, "email"],
          ["Password", "password", "password", true, "new-password"],
          [
            "Confirm password",
            "confirm_password",
            "password",
            true,
            "new-password",
          ],
        ].map(([label, name, type, required, autoComplete]) => (
          <label className="field" key={name}>
            {label}
            {required ? " *" : ""}
            <input
              name={name}
              type={type}
              required={required}
              maxLength={
                name.includes("password") ? 1024 : name === "email" ? 254 : 150
              }
              autoComplete={autoComplete}
              aria-invalid={!!errors[name]}
              aria-describedby={
                errors[name] ? `owner-${name}-error` : undefined
              }
            />
            {errors[name] && (
              <span id={`owner-${name}-error`} role="alert">
                {errors[name].join(" ")}
              </span>
            )}
          </label>
        ))}
      </fieldset>
      <p>
        Use at least 8 characters and avoid common passwords. After registration
        you will go directly to the dashboard. Registration closes permanently;
        later visits use the shared login page.
      </p>
      {error && (
        <div className="notice" role="alert">
          {error}
        </div>
      )}
      <button className="button primary" disabled={pending} type="submit">
        {pending ? "Creating Owner…" : "Create Owner account"}
      </button>
    </form>
  );
}
