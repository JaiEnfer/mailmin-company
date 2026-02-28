"use client";

import { useEffect, useState } from "react";
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
};

export default function SettingsPage() {
  const [role, setRole] = useState<string>("viewer");
  const [ws, setWs] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const canEdit = role === "admin";

  async function load() {
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

  useEffect(() => {
    const r = localStorage.getItem("mm_role") || "viewer";
    setRole(r);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function save() {
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

      {err ? <div className="rounded-xl border p-3 text-sm text-red-600">{err}</div> : null}
      {ok ? <div className="rounded-xl border p-3 text-sm text-green-700">{ok}</div> : null}

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Integrations
            <Badge variant="secondary" className="rounded-xl">Google</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm text-muted-foreground">
            Connect Gmail & Calendar so MailMind can draft replies and schedule meetings.
          </div>

          <Button
            className="rounded-xl"
            onClick={() => {
              // redirect user to backend OAuth start
              window.location.href = `${process.env.NEXT_PUBLIC_API_BASE}/auth/google/start`;
            }}
          >
            Connect Google
          </Button>

          <div className="text-xs text-muted-foreground">
            You’ll be redirected to Google for consent, then returned to MailMind.
          </div>
        </CardContent>
      </Card>


      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Workspace configuration
            <Button variant="secondary" className="rounded-xl" onClick={load}>
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
                  <Input value={ws.name} disabled />
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
                    value={ws.default_meeting_duration_minutes ?? 0}
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
                      If enabled, MailMind may execute certain actions automatically (later).
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

                <Button className="rounded-xl" onClick={save} disabled={!canEdit || saving}>
                  {saving ? "Saving…" : "Save changes"}
                </Button>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}