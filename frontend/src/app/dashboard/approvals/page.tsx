"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

type Approval = {
  id: number;
  status: string;
  subject?: string | null;
  from?: string | null;
  draft_reply?: string | null;
  action_type?: string | null;
  created_at?: string | null;
};

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [role, setRole] = useState<string>("viewer");

  const [syncLoading, setSyncLoading] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet("/mailmind/approvals?status=pending&limit=50");
      setItems(data.items || []);
    } catch (e: any) {
      setErr(e?.message || "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }

  async function handleSyncUnread() {
    setErr(null);
    setSyncMsg(null);
    setSyncLoading(true);

    try {
      const unread = await apiGet("/gmail/unread");
      const emails = unread?.items || [];

      if (emails.length === 0) {
        setSyncMsg("Fetched 0 unread emails.");
        return;
      }

      let queued = 0;
      for (const m of emails) {
        try {
          await apiPost(`/mailmind/queue?message_id=${encodeURIComponent(m.id)}`);
          queued++;
        } catch {
          // ignore individual failures so one bad email doesn't stop the batch
        }
      }

      setSyncMsg(`Queued ${queued} email(s) for approval.`);
      await load(); // refresh approvals list
    } catch (e: any) {
      setErr(e?.message || "Sync failed");
    } finally {
      setSyncLoading(false);
    }
  }

  useEffect(() => {
    const r = localStorage.getItem("mm_role") || "viewer";
    setRole(r);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function approve(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/approve`);
      await load();
    } catch (e: any) {
      setErr(e?.message || "Approve failed");
    }
  }

  async function send(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/send`);
      await load();
    } catch (e: any) {
      setErr(e?.message || "Send/Execute failed");
    }
  }

  const canAct = role === "admin" || role === "approver";

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Approvals</div>
          <div className="text-sm text-muted-foreground">
            Review what MailMind plans to do before it executes.
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            className="rounded-xl"
            onClick={handleSyncUnread}
            disabled={syncLoading}
          >
            {syncLoading ? "Syncing..." : "Sync Unread Emails"}
          </Button>

          <Button variant="secondary" className="rounded-xl" onClick={load}>
            Refresh
          </Button>
        </div>
      </div>

      {err ? (
        <div className="rounded-xl border p-3 text-sm text-red-600">{err}</div>
      ) : null}

      {syncMsg ? (
        <div className="rounded-xl border p-3 text-sm text-green-700">{syncMsg}</div>
      ) : null}

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Pending approvals
            <Badge variant="secondary" className="rounded-xl">
              {items.length}
            </Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading…</div>
          ) : null}

          {!loading && items.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No pending approvals.
            </div>
          ) : null}

          {items.map((a) => (
            <div key={a.id} className="rounded-2xl border p-4">
              <div className="flex flex-col justify-between gap-2 md:flex-row md:items-start">
                <div className="space-y-1">
                  <div className="text-sm font-medium">
                    {a.subject || "(No subject)"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {a.from || ""}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge className="rounded-xl" variant="outline">
                      {a.status}
                    </Badge>
                    {a.action_type ? (
                      <Badge className="rounded-xl" variant="secondary">
                        {a.action_type}
                      </Badge>
                    ) : null}
                  </div>
                </div>

                {canAct ? (
                  <div className="flex gap-2">
                    <Button className="rounded-xl" onClick={() => approve(a.id)}>
                      Approve
                    </Button>
                    <Button
                      className="rounded-xl"
                      variant="secondary"
                      onClick={() => send(a.id)}
                    >
                      Send / Execute
                    </Button>
                  </div>
                ) : (
                  <Badge variant="secondary" className="rounded-xl">
                    View only
                  </Badge>
                )}
              </div>

              <Separator className="my-3" />

              <div className="text-sm">
                <div className="text-xs font-medium text-muted-foreground">
                  Draft reply
                </div>
                <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-muted/40 p-3 text-sm">
                  {a.draft_reply || ""}
                </pre>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}