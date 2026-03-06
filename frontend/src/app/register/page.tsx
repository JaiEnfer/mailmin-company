"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";

import { setToken, registerWorkspace } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [workspace, setWorkspace] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit() {
    setErr(null);
    setLoading(true);

    try {
      const cleanWorkspace = workspace.trim();
      const cleanEmail = email.trim().toLowerCase();
      const cleanPassword = password;

      if (!cleanWorkspace) {
        throw new Error("Workspace name is required");
      }

      if (!cleanEmail) {
        throw new Error("Email is required");
      }

      if (cleanPassword.length < 8) {
        throw new Error("Password must be at least 8 characters");
      }

      const data = await registerWorkspace(
        cleanWorkspace,
        cleanEmail,
        cleanPassword
      );

      console.log("REGISTER SUCCESS DATA:", data);

      if (!data?.access_token) {
        throw new Error("Register succeeded but no access token was returned");
      }

      setToken(data.access_token);
      localStorage.setItem("mm_role", data?.user?.role || "admin");

      console.log("TOKEN SAVED, redirecting...");
      router.push("/dashboard/settings");
    } catch (e: any) {
      setErr(e?.message || "Register failed");
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
              <Input
                value={workspace}
                onChange={(e) => setWorkspace(e.target.value)}
                placeholder="Acme Inc."
              />
            </div>

            <div className="space-y-2">
              <Label>Admin email</Label>
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@acme.com"
              />
            </div>

            <div className="space-y-2">
              <Label>Password</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min 8 chars"
              />
            </div>

            {err ? <div className="text-sm text-red-600">{err}</div> : null}

            <Button
              onClick={onSubmit}
              disabled={loading}
              className="w-full rounded-xl"
            >
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