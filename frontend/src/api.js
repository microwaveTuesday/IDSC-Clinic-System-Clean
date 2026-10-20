export class ApiError extends Error {
  constructor(status, body) {
    super(body.detail || body.title || `Request failed (${status})`);
    this.status = status;
    this.body = body;
  }
}

const inflight = new Map();
const retryKeys = new Map();
export function request(path, method = "GET", body, options = {}) {
  if (method === "GET") return send(path, method, body);
  const signature = JSON.stringify([path, method, body, options]);
  if (inflight.has(signature)) return inflight.get(signature);
  const previous = retryKeys.get(signature);
  const key =
    previous && previous.expires > Date.now()
      ? previous.key
      : crypto.randomUUID();
  retryKeys.set(signature, { key, expires: Date.now() + 60000 });
  for (const [id, entry] of retryKeys)
    if (entry.expires < Date.now()) retryKeys.delete(id);
  const pending = send(path, method, body, key, options)
    .then((result) => {
      retryKeys.delete(signature);
      return result;
    })
    .finally(() => inflight.delete(signature));
  inflight.set(signature, pending);
  return pending;
}
async function send(path, method, body, key, options = {}) {
  const headers = { Accept: "application/json" };
  if (method !== "GET") {
    const csrf = await request("/api/auth/csrf/");
    headers["X-CSRFToken"] = csrf.csrfToken;
    headers["Content-Type"] = "application/json";
    headers["Idempotency-Key"] = key;
    if (options.version) headers["X-Record-Version"] = options.version;
  }
  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      credentials: "include",
      signal: AbortSignal.timeout(30000),
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new ApiError(0, {
      detail:
        "The server did not respond. Check your connection and retry; your submission key will be reused.",
    });
  }
  const data =
    response.status === 204
      ? null
      : await response.json().catch(() => ({
          detail: "The server returned an unreadable response.",
        }));
  if (!response.ok) {
    if (response.status === 401 && path !== "/api/auth/login/") {
      window.dispatchEvent(new Event("clinic-session-expired"));
    }
    if (response.status === 403 && /csrf/i.test(data.detail || "")) {
      data.detail = "Your security token expired. Reload the page and try again. Your change was not submitted.";
    }
    throw new ApiError(response.status, data);
  }
  return data;
}

export async function listAll(resource) {
  const result = [];
  for (let page = 1; ; page++) {
    const data = await request(
      `/api/v1/${resource}/?page=${page}&page_size=100`,
    );
    if (Array.isArray(data)) return data;
    result.push(...data.results);
    if (page >= data.total_pages) return result;
  }
}
