const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export function setToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem("mm_token", token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mm_token");
}

export async function apiGet(path: string) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiPost(path: string) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiPostQuery(path: string, query: Record<string, any>) {
  const token = getToken();
  const qs = new URLSearchParams();
  Object.entries(query).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    qs.set(k, String(v));
  });

  const res = await fetch(`${API_BASE}${path}?${qs.toString()}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) {
    let msg = `POST ${path} failed: ${res.status}`;
    try {
      const data = await res.json();
      msg = data?.detail || msg;
    } catch {}
    throw new Error(msg);
  }

  return res.json();
}