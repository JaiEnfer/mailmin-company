"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@demo.co");
  const [password, setPassword] = useState("Pass1234!");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit() {
    setErr(null);
    setLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      const url = `${apiBase}/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `Login failed (${res.status})`);

      setToken(data.access_token);
      localStorage.setItem("mm_role", data.user.role);
      router.push("/dashboard/approvals");
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
                Access approvals, audit trails, and automation settings.
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
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
            <div className="text-sm text-muted-foreground">Replynto</div>
            <div className="mt-2 text-3xl font-semibold tracking-tight">
              Your AI employee for email + tasks
            </div>
            <div className="mt-3 text-sm text-muted-foreground">
              Approval-first automation with full audit logs. Draft replies, schedule meetings,
              and execute workflows safely.
            </div>

            <div className="mt-6 space-y-3 text-sm">
              <div className="rounded-xl bg-muted/40 p-3">
                <div className="font-medium">✅ Approval workflow</div>
                <div className="text-muted-foreground">Humans stay in control.</div>
              </div>
              <div className="rounded-xl bg-muted/40 p-3">
                <div className="font-medium">✅ Audit trail</div>
                <div className="text-muted-foreground">Every action is logged per workspace.</div>
              </div>
              <div className="rounded-xl bg-muted/40 p-3">
                <div className="font-medium">✅ Cross-app tasks</div>
                <div className="text-muted-foreground">Calendar events + more coming next.</div>
              </div>
            </div>

            <div className="mt-6 text-xs text-muted-foreground">
              Next: Connect your workspace, review approvals, and let Replynto execute actions.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}