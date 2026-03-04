"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { setToken, API_BASE } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit() {
    setErr(null);
    setLoading(true);
    try {
      const url = `${API_BASE}/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `Login failed (${res.status})`);

      setToken(data.access_token);
      localStorage.setItem("mm_role", data.user.role);
      router.push("/dashboard");
    } catch (e: any) {
      setErr(e.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center p-4">
        <div className="grid w-full grid-cols-1 gap-6 md:grid-cols-2">
          <Card className="rounded-2xl border shadow-sm">
            <CardHeader>
              <CardTitle className="text-2xl">Sign in</CardTitle>
              <div className="text-sm text-muted-foreground">
                Approvals, audit logs, and automation settings.
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
              </div>
              <div className="space-y-2">
                <Label>Password</Label>
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
              </div>

              {err ? <div className="text-sm text-red-600">{err}</div> : null}

              <Button onClick={onSubmit} disabled={loading} className="w-full rounded-xl">
                {loading ? "Signing in..." : "Sign in"}
              </Button>

              <div className="text-center text-xs text-muted-foreground">
                Don’t have an account?{" "}
                <Link href="/register" className="underline underline-offset-4">
                  Create a workspace
                </Link>
              </div>
            </CardContent>
          </Card>

          <div className="rounded-2xl border bg-card p-6 shadow-sm">
            <div className="text-sm text-muted-foreground">MailMind</div>
            <div className="mt-2 text-3xl font-semibold tracking-tight">
              Your AI employee for email + tasks
            </div>
            <div className="mt-3 text-sm text-muted-foreground">
              Approval-first automation with full audit logs. Draft replies, schedule meetings,
              and execute actions safely.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}