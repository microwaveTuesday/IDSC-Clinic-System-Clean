import { useState } from "react";
import { request } from "./api";
import { Modal, Button } from "./ClinicUI";

export function PasswordChangeDialog({ onClose, onSuccess, onExpired }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});
  async function submit(event) {
    event.preventDefault();
    if (pending) return;
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    setError("");
    setErrors({});
    if (data.new_password !== data.confirm_password) {
      setErrors({ confirm_password: ["The new passwords do not match."] });
      return;
    }
    setPending(true);
    try {
      await request("/api/auth/password/change/", "POST", data);
      form.reset();
      onSuccess();
    } catch (e) {
      if (e.status === 401) {
        form.reset();
        onExpired();
      } else {
        setError(e.message);
        setErrors(e.body?.errors || {});
      }
    } finally {
      setPending(false);
    }
  }
  return (
    <Modal
      title="Change password"
      onClose={() => {
        if (!pending) onClose();
      }}
    >
      <form onSubmit={submit} aria-busy={pending}>
        <div className="modal-content">
          <p className="password-help" id="password-help">
            Use at least 8 characters. Avoid common passwords, numbers alone,
            and passwords similar to your account details. Your new password
            must differ from your current one.
          </p>
          {error && (
            <div className="notice" role="alert">
              {error}
            </div>
          )}
          <fieldset className="password-fields" disabled={pending}>
            {[
              ["current_password", "Current password", "current-password"],
              ["new_password", "New password", "new-password"],
              ["confirm_password", "Confirm new password", "new-password"],
            ].map(([name, label, autocomplete]) => (
              <div className="field" key={name}>
                <label htmlFor={`password-${name}`}>{label}</label>
                <input
                  id={`password-${name}`}
                  name={name}
                  type="password"
                  autoComplete={autocomplete}
                  required
                  maxLength={1024}
                  minLength={name === "current_password" ? undefined : 8}
                  aria-invalid={Boolean(errors[name])}
                  aria-describedby={
                    errors[name] ? `${name}-error` : "password-help"
                  }
                />
                {errors[name] && (
                  <span
                    className="password-error"
                    id={`${name}-error`}
                    role="alert"
                  >
                    {[].concat(errors[name]).join(" ")}
                  </span>
                )}
              </div>
            ))}
          </fieldset>
          <p className="password-help">
            You’ll stay signed in here. Your other sessions will be signed out.
          </p>
        </div>
        <div className="modal-actions">
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button type="submit" disabled={pending}>
            {pending ? "Updating…" : "Update password"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export function UsernameChangeDialog({
  onClose,
  onSuccess,
  onExpired,
  username,
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});
  async function submit(event) {
    event.preventDefault();
    if (pending) return;
    const form = event.currentTarget;
    setPending(true);
    setError("");
    setErrors({});
    try {
      const user = await request(
        "/api/auth/username/change/",
        "POST",
        Object.fromEntries(new FormData(form)),
      );
      form.reset();
      onSuccess(user);
    } catch (e) {
      if (e.status === 401) {
        form.reset();
        onExpired();
      } else {
        setError(e.message);
        setErrors(e.body?.errors || {});
      }
    } finally {
      setPending(false);
    }
  }
  return (
    <Modal
      title="Change username"
      onClose={() => {
        if (!pending) onClose();
      }}
    >
      <form onSubmit={submit} aria-busy={pending}>
        <div className="modal-content">
          <p className="password-help">
            Your current username is <strong>{username}</strong>. You’ll stay
            signed in here and use the new username the next time you sign in.
          </p>
          {error && (
            <div className="notice" role="alert">
              {error}
            </div>
          )}
          <fieldset className="password-fields" disabled={pending}>
            <div className="field">
              <label htmlFor="account-new-username">New username</label>
              <input
                id="account-new-username"
                name="new_username"
                autoComplete="username"
                required
                maxLength={150}
                aria-invalid={Boolean(errors.new_username)}
                aria-describedby={
                  errors.new_username ? "new-username-error" : "username-help"
                }
              />
              {errors.new_username && (
                <span
                  id="new-username-error"
                  className="password-error"
                  role="alert"
                >
                  {[].concat(errors.new_username).join(" ")}
                </span>
              )}
            </div>
            <div className="field">
              <label htmlFor="username-current-password">
                Current password
              </label>
              <input
                id="username-current-password"
                name="current_password"
                type="password"
                autoComplete="current-password"
                required
                maxLength={1024}
                aria-invalid={Boolean(errors.current_password)}
                aria-describedby={
                  errors.current_password
                    ? "username-password-error"
                    : undefined
                }
              />
              {errors.current_password && (
                <span
                  id="username-password-error"
                  className="password-error"
                  role="alert"
                >
                  {[].concat(errors.current_password).join(" ")}
                </span>
              )}
            </div>
          </fieldset>
          <p id="username-help" className="password-help">
            Up to 150 characters: letters, numbers, and @ . + - _ symbols.
            Choose a username that is not already in use.
          </p>
        </div>
        <div className="modal-actions">
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button type="submit" disabled={pending}>
            {pending ? "Updating…" : "Update username"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
