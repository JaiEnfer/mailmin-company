"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPostQuery } from "@/lib/api";

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

type Tab = "pending" | "approved" | "executed";

export default function ApprovalsPage() {
  // ✅ Hooks always in the same order
  const [mounted, setMounted] = useState(false);

  const [tab, setTab] = useState<Tab>("pending");

  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [role, setRole] = useState<string>("viewer");
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  async function load(nextTab?: Tab) {
    setErr(null);
    setLoading(true);

    const t = nextTab ?? tab;

    try {
      const data = await apiGet(`/mailmind/approvals?status=${encodeURIComponent(t)}&limit=50`);
      setItems(data.items || []);
    } catch (e: any) {
      setErr(e?.message || "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!mounted) return;

    const r = localStorage.getItem("mm_role") || "viewer";
    setRole(r);

    load("pending");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  async function handleSyncUnread() {
    setErr(null);
    setSyncing(true);
    try {
      const data = await apiPostQuery("/mailmind/sync-unread", { limit: 10 });
      // After sync, show pending list
      setTab("pending");
      await load("pending");
      alert(`Fetched ${data.fetched}, created ${data.created} approvals`);
    } catch (e: any) {
      setErr(e?.message || "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  async function approve(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/approve`);
      // After approving, move to approved tab so user sees it
      setTab("approved");
      await load("approved");
    } catch (e: any) {
      setErr(e?.message || "Approve failed");
    }
  }

  async function executeAction(id: number) {
    setErr(null);
    try {
      // Backend: /send is now execute-only
      await apiPost(`/mailmind/approvals/${id}/send`);
      // After execute, show executed tab
      setTab("executed");
      await load("executed");
    } catch (e: any) {
      setErr(e?.message || "Execute failed");
    }
  }

  async function sendReply(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/reply`);
      // After sending reply, refresh current tab (or jump to executed/sent later)
      await load();
    } catch (e: any) {
      setErr(e?.message || "Send reply failed");
    }
  }

  const canAct = role === "admin" || role === "approver";

  if (!mounted) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Approvals</div>
          <div className="text-sm text-muted-foreground">
            Approval-first automation. Execute actions and send replies separately.
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            className="rounded-xl"
            onClick={handleSyncUnread}
            disabled={syncing}
          >
            {syncing ? "Syncing…" : "Sync Unread"}
          </Button>

          <Button variant="secondary" className="rounded-xl" onClick={() => load()}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={tab === "pending" ? "default" : "secondary"}
          className="rounded-xl"
          onClick={() => setTab("pending")}
        >
          Pending
        </Button>
        <Button
          variant={tab === "approved" ? "default" : "secondary"}
          className="rounded-xl"
          onClick={() => setTab("approved")}
        >
          Approved
        </Button>
        <Button
          variant={tab === "executed" ? "default" : "secondary"}
          className="rounded-xl"
          onClick={() => setTab("executed")}
        >
          Executed
        </Button>
      </div>

      {err ? (
        <div className="rounded-xl border p-3 text-sm text-red-600 whitespace-pre-wrap">
          {err}
        </div>
      ) : null}

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            {tab.charAt(0).toUpperCase() + tab.slice(1)} approvals
            <Badge variant="secondary" className="rounded-xl">
              {items.length}
            </Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          {loading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}

          {!loading && items.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No items in <span className="font-medium">{tab}</span>.{" "}
              {tab === "pending" ? (
                <>
                  Click <span className="font-medium">Sync Unread</span> to fetch emails and create
                  approvals.
                </>
              ) : null}
            </div>
          ) : null}

          {items.map((a) => {
            const showApprove = canAct && a.status === "pending";
            const showExecute = canAct && (a.status === "approved"); // execute only after approve
            const showReply = canAct && (a.status === "approved" || a.status === "executed"); // reply after approve/execute

            return (
              <div key={a.id} className="rounded-2xl border p-4">
                <div className="flex flex-col justify-between gap-2 md:flex-row md:items-start">
                  <div className="space-y-1">
                    <div className="text-sm font-medium">{a.subject || "(No subject)"}</div>
                    <div className="text-xs text-muted-foreground">{a.from || ""}</div>
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
                    <div className="flex flex-wrap gap-2">
                      {showApprove ? (
                        <Button className="rounded-xl" onClick={() => approve(a.id)}>
                          Approve
                        </Button>
                      ) : null}

                      {showExecute ? (
                        <Button
                          className="rounded-xl"
                          variant="secondary"
                          onClick={() => executeAction(a.id)}
                        >
                          Execute Action
                        </Button>
                      ) : null}

                      {showReply ? (
                        <Button className="rounded-xl" onClick={() => sendReply(a.id)}>
                          Send Reply
                        </Button>
                      ) : null}

                      {!showApprove && !showExecute && !showReply ? (
                        <Badge variant="secondary" className="rounded-xl">
                          No actions available
                        </Badge>
                      ) : null}
                    </div>
                  ) : (
                    <Badge variant="secondary" className="rounded-xl">
                      View only
                    </Badge>
                  )}
                </div>

                <Separator className="my-3" />

                <div className="text-sm">
                  <div className="text-xs font-medium text-muted-foreground">Draft reply</div>
                  <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-muted/40 p-3 text-sm">
                    {a.draft_reply || ""}
                  </pre>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}