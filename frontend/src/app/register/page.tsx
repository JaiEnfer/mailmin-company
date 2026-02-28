"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();

  const [alreadyLoggedIn, setAlreadyLoggedIn] = useState(false);

  const [workspaceName, setWorkspaceName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("mm_token");
    setAlreadyLoggedIn(!!token);
  }, []);

  function logout() {
    localStorage.removeItem("mm_token");
    localStorage.removeItem("mm_role");
    // stay on /register after logout
    window.location.href = "/register";
  }

  async function submit() {
    setErr(null);

    if (!workspaceName.trim()) return setErr("Workspace name is required");
    if (!email.trim()) return setErr("Email is required");
    if (!password.trim()) return setErr("Password is required");

    setLoading(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE;
      if (!base) throw new Error("Missing NEXT_PUBLIC_API_BASE");

      const url =
        `${base}/auth/register` +
        `?workspace_name=${encodeURIComponent(workspaceName.trim())}` +
        `&email=${encodeURIComponent(email.trim())}` +
        `&password=${encodeURIComponent(password)}`;

      const res = await fetch(url, { method: "POST" });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || "Registration failed");
      }

      const data = await res.json();

      // store token + role (consistent with login)
      localStorage.setItem("mm_token", data.access_token);
      localStorage.setItem("mm_role", data.user?.role || "admin");

      router.push("/dashboard/approvals");
    } catch (e: any) {
      setErr(e?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  // ✅ Permanent: if already logged in, DO NOT redirect.
  // Show a clear message and a logout button.
  if (alreadyLoggedIn) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-sm space-y-4">
          <div>
            <div className="text-2xl font-semibold tracking-tight">Create your workspace</div>
            <div className="text-sm text-muted-foreground">
              You’re currently signed in. To create a new company/workspace, log out first.
            </div>
          </div>

          <button
            onClick={logout}
            className="h-10 w-full rounded-xl bg-primary text-primary-foreground text-sm font-medium"
          >
            Log out
          </button>

          <div className="text-sm text-muted-foreground text-center">
            Or go to{" "}
            <Link className="underline underline-offset-4" href="/dashboard/approvals">
              Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Normal register form (not logged in)
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-sm space-y-4">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Create your workspace</div>
          <div className="text-sm text-muted-foreground">
            Start using MailMind for your company in minutes.
          </div>
        </div>

        {err ? <div className="rounded-xl border p-3 text-sm text-red-600">{err}</div> : null}

        <div className="space-y-2">
          <label className="text-sm font-medium">Workspace name</label>
          <input
            className="h-10 w-full rounded-xl border bg-background px-3 text-sm"
            value={workspaceName}
            onChange={(e) => setWorkspaceName(e.target.value)}
            placeholder="Acme Inc"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Admin email</label>
          <input
            className="h-10 w-full rounded-xl border bg-background px-3 text-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@acme.com"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Password</label>
          <input
            type="password"
            className="h-10 w-full rounded-xl border bg-background px-3 text-sm"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Choose a strong password"
          />
          <div className="text-xs text-muted-foreground">
            Tip: Use at least 10 characters.
          </div>
        </div>

        <button
          onClick={submit}
          disabled={loading}
          className="h-10 w-full rounded-xl bg-primary text-primary-foreground text-sm font-medium disabled:opacity-60"
        >
          {loading ? "Creating…" : "Create workspace"}
        </button>

        <div className="text-sm text-muted-foreground text-center">
          Already have an account?{" "}
          <Link className="underline underline-offset-4" href="/login">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}