export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("mm_token", token);
  }
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mm_token");
}

function getErrorMessage(data: any, status: number) {
  if (typeof data?.detail === "string") return data.detail;
  if (data?.detail) return JSON.stringify(data.detail);
  if (typeof data?.message === "string") return data.message;
  return `Request failed (${status})`;
}

export async function apiGet(path: string) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  const text = await res.text();
  let data: any = {};
  try {
    data = JSON.parse(text);
  } catch {}

  if (!res.ok) throw new Error(getErrorMessage(data, res.status));

  return data;
}

export async function apiPost(path: string, body?: any) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data: any = {};
  try {
    data = JSON.parse(text);
  } catch {}

  if (!res.ok) throw new Error(getErrorMessage(data, res.status));

  return data;
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

  const text = await res.text();
  let data: any = {};
  try {
    data = JSON.parse(text);
  } catch {}

  if (!res.ok) throw new Error(getErrorMessage(data, res.status));

  return data;
}