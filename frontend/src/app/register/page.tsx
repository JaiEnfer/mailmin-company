"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";

import { setToken, API_BASE } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [workspace, setWorkspace] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [API_BASE] = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  async function onSubmit() {
    setErr(null);
    setLoading(true);
    try {
      const url =
        `${API_BASE}/auth/register?workspace_name=${encodeURIComponent(workspace)}` +
        `&email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;

      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `Register failed (${res.status})`);

      setToken(data.access_token);
      localStorage.setItem("mm_role", data.user.role);
      router.push("/dashboard/settings");
    } catch (e: any) {
      setErr(e.message || "Register failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen max-w-xl items-center justify-center p-4">
        <Card className="w-full rounded-2xl border shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl">Create workspace</CardTitle>
            <div className="text-sm text-muted-foreground">
              You become the admin of this workspace.
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Company / Workspace name</Label>
              <Input value={workspace} onChange={(e) => setWorkspace(e.target.value)} placeholder="Acme Inc." />
            </div>
            <div className="space-y-2">
              <Label>Admin email</Label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@acme.com" />
            </div>
            <div className="space-y-2">
              <Label>Password</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 chars" />
            </div>

            {err ? <div className="text-sm text-red-600">{err}</div> : null}

            <Button onClick={onSubmit} disabled={loading} className="w-full rounded-xl">
              {loading ? "Creating..." : "Create workspace"}
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="underline underline-offset-4">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}