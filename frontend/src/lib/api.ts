export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("mm_token", token);
  }
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mm_token");
}

function parseMaybeJson(text: string) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function getErrorMessage(data: any, text: string, status: number) {
  if (typeof data?.detail === "string") return data.detail;
  if (data?.detail) return JSON.stringify(data.detail);
  if (typeof data?.message === "string") return data.message;
  if (text) return text;
  return `Request failed (${status})`;
}

async function handleResponse(res: Response) {
  const text = await res.text();
  const data = parseMaybeJson(text);

  if (!res.ok) {
    throw new Error(getErrorMessage(data, text, res.status));
  }

  return data;
}

export async function apiGet(path: string) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  return handleResponse(res);
}

export async function apiPost(path: string, body?: any) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  return handleResponse(res);
}

export async function apiPostQuery(path: string, params: Record<string, any>) {
  const query = new URLSearchParams(params).toString();
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}?${query}`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  return handleResponse(res);
}

export async function registerWorkspace(
  workspace_name: string,
  email: string,
  password: string
) {
  const query =
    `workspace_name=${encodeURIComponent(workspace_name)}` +
    `&email=${encodeURIComponent(email)}` +
    `&password=${encodeURIComponent(password)}`;

  const res = await fetch(`${API_BASE}/auth/register?${query}`, {
    method: "POST",
  });

  return handleResponse(res);
}