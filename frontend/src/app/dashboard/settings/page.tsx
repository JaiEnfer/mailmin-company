"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPostQuery } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

type Workspace = {
  id: number;
  name: string;
  timezone: string;
  default_meeting_duration_minutes: number;
  company_tone: string;
  auto_execute_actions: boolean;
  google_email?: string | null;
};

type CreateUserForm = {
  email: string;
  password: string;
  role: "viewer" | "approver" | "admin";
};

type TeamUser = {
  id: number;
  email: string;
  role: "admin" | "approver" | "viewer";
  is_active: boolean;
  workspace_id?: number;
};

export default function SettingsPage() {
  const [mounted, setMounted] = useState(false);

  const [role, setRole] = useState<string>("viewer");
  const canEdit = role === "admin";

  const [ws, setWs] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const [googleConnected, setGoogleConnected] = useState<boolean | null>(null);

  // Team management (admin only)
  const [teamSaving, setTeamSaving] = useState(false);
  const [teamOk, setTeamOk] = useState<string | null>(null);
  const [teamErr, setTeamErr] = useState<string | null>(null);

  const [users, setUsers] = useState<TeamUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  const [newUser, setNewUser] = useState<CreateUserForm>({
    email: "",
    password: "",
    role: "viewer",
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const r = localStorage.getItem("mm_role") || "viewer";
    setRole(r);
  }, [mounted]);

  async function loadWorkspace() {
    setErr(null);
    setOk(null);
    setLoading(true);
    try {
      const data = await apiGet("/workspace/me");
      setWs(data);
    } catch (e: any) {
      setErr(e?.message || "Failed to load workspace settings");
    } finally {
      setLoading(false);
    }
  }

  async function loadGoogleStatus() {
    try {
      const data = await apiGet("/integrations/google/status");
      setGoogleConnected(!!data.connected);
    } catch {
      setGoogleConnected(false);
    }
  }

  async function loadUsers() {
    if (role !== "admin") return;
    setUsersLoading(true);
    try {
      const data = await apiGet("/users");
      setUsers(data.items || []);
    } catch {
      // keep silent
    } finally {
      setUsersLoading(false);
    }
  }

  useEffect(() => {
    if (!mounted) return;
    loadWorkspace();
    loadGoogleStatus();
    // role might not be set yet; we'll refresh users in a separate effect below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;
    if (role === "admin") loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted, role]);

  async function saveWorkspace() {
    if (!ws) return;
    setErr(null);
    setOk(null);
    setSaving(true);
    try {
      const updated = await apiPostQuery("/workspace/me", {
        timezone: ws.timezone,
        default_meeting_duration_minutes: ws.default_meeting_duration_minutes,
        company_tone: ws.company_tone,
        auto_execute_actions: ws.auto_execute_actions,
      });
      setWs(updated);
      setOk("Saved successfully.");
    } catch (e: any) {
      setErr(e?.message || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function connectGoogle() {
    setErr(null);
    setOk(null);
    try {
      const token = localStorage.getItem("mm_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/auth/google/start`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Failed to start Google OAuth");
      window.location.href = data.auth_url;
    } catch (e: any) {
      setErr(e?.message || "Google connect failed");
    }
  }

  async function createTeamUser() {
    setTeamOk(null);
    setTeamErr(null);

    if (!newUser.email.trim()) {
      setTeamErr("Email is required.");
      return;
    }
    if (!newUser.password || newUser.password.length < 8) {
      setTeamErr("Password must be at least 8 characters.");
      return;
    }

    setTeamSaving(true);
    try {
      const created = await apiPostQuery("/users/create", {
        email: newUser.email.trim(),
        password: newUser.password,
        role: newUser.role,
      });

      setTeamOk(`User created: ${created.email} (${created.role})`);
      setNewUser({ email: "", password: "", role: "viewer" });
      await loadUsers();
    } catch (e: any) {
      setTeamErr(e?.message || "Failed to create user");
    } finally {
      setTeamSaving(false);
    }
  }

  const googleBadge = useMemo(() => {
    if (googleConnected === null) return "Checking…";
    return googleConnected ? "✅ Google Connected" : "❌ Google Not Connected";
  }, [googleConnected]);

  if (!mounted) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Settings</div>
          <div className="text-sm text-muted-foreground">
            Configure MailMind behavior for your workspace.
          </div>
        </div>
        <Badge variant="secondary" className="rounded-xl">
          Role: {role}
        </Badge>
      </div>

      {err ? (
        <div className="rounded-xl border p-3 text-sm text-red-600 whitespace-pre-wrap">{err}</div>
      ) : null}
      {ok ? (
        <div className="rounded-xl border p-3 text-sm text-green-700 whitespace-pre-wrap">{ok}</div>
      ) : null}

      {/* Google Integration */}
      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Google Integration
            <Badge variant="secondary" className="rounded-xl">
              {googleBadge}
            </Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">
            Connect Gmail + Calendar so MailMind can sync unread emails and book meetings.
          </div>

          <div className="flex gap-2">
            <Button onClick={connectGoogle} className="rounded-xl">
              {googleConnected ? "Reconnect Google" : "Connect Google"}
            </Button>
            <Button variant="secondary" className="rounded-xl" onClick={loadGoogleStatus}>
              Refresh status
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Workspace config */}
      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Workspace configuration
            <Button variant="secondary" className="rounded-xl" onClick={loadWorkspace}>
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {loading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}

          {!loading && ws ? (
            <>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Workspace name</Label>
                  <Input value={ws.name ?? ""} disabled />
                </div>

                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Input
                    value={ws.timezone ?? ""}
                    onChange={(e) => setWs({ ...ws, timezone: e.target.value })}
                    disabled={!canEdit}
                    placeholder="Europe/Berlin"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Default meeting duration (minutes)</Label>
                  <Input
                    type="number"
                    value={ws.default_meeting_duration_minutes ?? 30}
                    onChange={(e) =>
                      setWs({ ...ws, default_meeting_duration_minutes: Number(e.target.value) })
                    }
                    disabled={!canEdit}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Auto execute actions</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      type="checkbox"
                      checked={ws.auto_execute_actions ?? false}
                      onChange={(e) => setWs({ ...ws, auto_execute_actions: e.target.checked })}
                      disabled={!canEdit}
                      className="h-4 w-4"
                    />
                    <span className="text-sm text-muted-foreground">
                      (Optional) Later: allow safe auto-execution for low-risk actions.
                    </span>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Company tone (used for draft replies)</Label>
                <Textarea
                  value={ws.company_tone ?? ""}
                  onChange={(e) => setWs({ ...ws, company_tone: e.target.value })}
                  disabled={!canEdit}
                  rows={5}
                />
                <div className="text-xs text-muted-foreground">
                  Example: “Friendly, concise, and professional. Avoid hype. Ask one clear question at a time.”
                </div>
              </div>

              <div className="flex items-center justify-between">
                {!canEdit ? (
                  <Badge variant="secondary" className="rounded-xl">
                    View only (admin required to edit)
                  </Badge>
                ) : (
                  <div className="text-xs text-muted-foreground">
                    Changes apply to future drafts and action proposals.
                  </div>
                )}

                <Button className="rounded-xl" onClick={saveWorkspace} disabled={!canEdit || saving}>
                  {saving ? "Saving…" : "Save changes"}
                </Button>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>

      {/* Team management */}
      {role === "admin" ? (
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle>Team management</CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Add teammates to this workspace. Approvers can approve/execute, viewers can only view.
            </div>

            {teamErr ? (
              <div className="rounded-xl border p-3 text-sm text-red-600 whitespace-pre-wrap">
                {teamErr}
              </div>
            ) : null}
            {teamOk ? (
              <div className="rounded-xl border p-3 text-sm text-green-700 whitespace-pre-wrap">
                {teamOk}
              </div>
            ) : null}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="user@company.com"
                />
              </div>

              <div className="space-y-2">
                <Label>Temporary password</Label>
                <Input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="Min 8 chars"
                />
              </div>

              <div className="space-y-2">
                <Label>Role</Label>
                <select
                  className="h-10 w-full rounded-xl border bg-background px-3 text-sm"
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value as any })}
                >
                  <option value="viewer">Viewer</option>
                  <option value="approver">Approver</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-xs text-muted-foreground">
                Tip: Use “approver” for teammates who can execute actions.
              </div>

              <Button className="rounded-xl" onClick={createTeamUser} disabled={teamSaving}>
                {teamSaving ? "Creating…" : "Create user"}
              </Button>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Users</div>
                <Button
                  variant="secondary"
                  className="rounded-xl"
                  onClick={loadUsers}
                  disabled={usersLoading}
                >
                  {usersLoading ? "Refreshing…" : "Refresh users"}
                </Button>
              </div>

              {users.length === 0 ? (
                <div className="text-sm text-muted-foreground">No users found.</div>
              ) : (
                <div className="overflow-hidden rounded-xl border">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/40">
                      <tr>
                        <th className="px-3 py-2 text-left">Email</th>
                        <th className="px-3 py-2 text-left">Role</th>
                        <th className="px-3 py-2 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id} className="border-t">
                          <td className="px-3 py-2">{u.email}</td>
                          <td className="px-3 py-2">
                            <Badge variant="secondary" className="rounded-xl">
                              {u.role}
                            </Badge>
                          </td>
                          <td className="px-3 py-2">
                            {u.is_active ? (
                              <Badge className="rounded-xl" variant="outline">
                                active
                              </Badge>
                            ) : (
                              <Badge className="rounded-xl" variant="secondary">
                                disabled
                              </Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle>Team management</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary" className="rounded-xl">
              View only (admin required)
            </Badge>
          </CardContent>
        </Card>
      )}
    </div>
  );
}