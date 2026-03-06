"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

type UserRow = {
  id: number;
  email: string;
  role: "admin" | "approver" | "viewer";
  is_active: boolean;
  created_at?: string | null;
};

export default function UsersPage() {
  const [role, setRole] = useState<string>("viewer");
  const [items, setItems] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("Pass1234!");
  const [newRole, setNewRole] = useState<"admin" | "approver" | "viewer">("viewer");
  const [creating, setCreating] = useState(false);

  const canAdmin = role === "admin";

  function getErrorMessage(e: any) {
    if (!e) return "Request failed";
    if (typeof e === "string") return e;
    if (e?.message && typeof e.message === "string") return e.message;
    if (e?.detail) {
      if (typeof e.detail === "string") return e.detail;
      return JSON.stringify(e.detail);
    }
    return JSON.stringify(e);
  }

  async function load() {
    setErr(null);
    setOk(null);
    setLoading(true);

    try {
      const data = await apiGet("/admin/users");
      setItems(data.items || []);
    } catch (e: any) {
      setErr(getErrorMessage(e) || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setRole(localStorage.getItem("mm_role") || "viewer");
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createUser() {
    setErr(null);
    setOk(null);

    if (!email.trim()) {
      setErr("Email is required");
      return;
    }

    setCreating(true);
    try {
      await apiPost("/admin/users", {
        email: email.trim(),
        password,
        role: newRole,
      });

      setOk("User created.");
      setEmail("");
      setPassword("Pass1234!");
      setNewRole("viewer");
      await load();
    } catch (e: any) {
      setErr(getErrorMessage(e) || "Create user failed");
    } finally {
      setCreating(false);
    }
  }

  async function disableUser(userId: number) {
    setErr(null);
    setOk(null);

    try {
      await apiPost(`/admin/users/${userId}/disable`, {});
      setOk("User disabled.");
      await load();
    } catch (e: any) {
      setErr(getErrorMessage(e) || "Disable failed");
    }
  }

  async function changeRole(userId: number, r: "admin" | "approver" | "viewer") {
    setErr(null);
    setOk(null);

    try {
      await apiPost(`/admin/users/${userId}/role`, { role: r });
      setOk("Role updated.");
      await load();
    } catch (e: any) {
      setErr(getErrorMessage(e) || "Role update failed");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Users</div>
          <div className="text-sm text-muted-foreground">
            Manage users and roles for your workspace.
          </div>
        </div>
        <Badge variant="secondary" className="rounded-xl">
          Role: {role}
        </Badge>
      </div>

      {err ? (
        <div className="rounded-xl border p-3 text-sm text-red-600">{err}</div>
      ) : null}

      {ok ? (
        <div className="rounded-xl border p-3 text-sm text-green-700">{ok}</div>
      ) : null}

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Create user
            {!canAdmin ? (
              <Badge variant="secondary" className="rounded-xl">
                Admin only
              </Badge>
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!canAdmin ? (
            <div className="text-sm text-muted-foreground">
              Only admins can create/disable users or change roles.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="space-y-2 md:col-span-1">
                  <Label>Email</Label>
                  <Input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="user@company.com"
                  />
                </div>

                <div className="space-y-2 md:col-span-1">
                  <Label>Temp password</Label>
                  <Input
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <div className="text-xs text-muted-foreground">
                    User can change later (we’ll add “change password” next).
                  </div>
                </div>

                <div className="space-y-2 md:col-span-1">
                  <Label>Role</Label>
                  <select
                    className="h-10 w-full rounded-xl border bg-background px-3 text-sm"
                    value={newRole}
                    onChange={(e) =>
                      setNewRole(e.target.value as "admin" | "approver" | "viewer")
                    }
                  >
                    <option value="viewer">viewer</option>
                    <option value="approver">approver</option>
                    <option value="admin">admin</option>
                  </select>
                </div>
              </div>

              <Button className="rounded-xl" onClick={createUser} disabled={creating}>
                {creating ? "Creating…" : "Create user"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Workspace users
            <Button variant="secondary" className="rounded-xl" onClick={load}>
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          {loading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}

          {!loading && items.length === 0 ? (
            <div className="text-sm text-muted-foreground">No users found.</div>
          ) : null}

          {items.map((u) => (
            <div key={u.id} className="rounded-2xl border p-4">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div className="space-y-1">
                  <div className="text-sm font-medium">{u.email}</div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="rounded-xl">
                      {u.role}
                    </Badge>
                    <Badge variant="secondary" className="rounded-xl">
                      {u.is_active ? "active" : "disabled"}
                    </Badge>
                  </div>
                </div>

                {canAdmin ? (
                  <div className="flex flex-wrap gap-2">
                    <select
                      className="h-10 rounded-xl border bg-background px-3 text-sm"
                      value={u.role}
                      onChange={(e) =>
                        changeRole(
                          u.id,
                          e.target.value as "admin" | "approver" | "viewer"
                        )
                      }
                      disabled={!u.is_active}
                    >
                      <option value="viewer">viewer</option>
                      <option value="approver">approver</option>
                      <option value="admin">admin</option>
                    </select>

                    <Button
                      variant="secondary"
                      className="rounded-xl"
                      onClick={() => disableUser(u.id)}
                      disabled={!u.is_active}
                    >
                      Disable
                    </Button>
                  </div>
                ) : (
                  <Badge variant="secondary" className="rounded-xl">
                    View only
                  </Badge>
                )}
              </div>

              <Separator className="my-3" />

              <div className="text-xs text-muted-foreground">
                User ID: {u.id}
                {u.created_at ? ` • Created: ${u.created_at}` : ""}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}