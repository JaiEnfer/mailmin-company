"use client";

import { useEffect, useMemo, useState } from "react";
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

function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  return (
    <Badge className="rounded-xl" variant={s === "pending" ? "outline" : "secondary"}>
      {status}
    </Badge>
  );
}

function Section({
  title,
  count,
  children,
  defaultOpen = false,
}: {
  title: string;
  count: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Card className="rounded-2xl shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left"
      >
        <CardHeader className="cursor-pointer select-none">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span>{title}</span>
              <span className="text-xs text-muted-foreground">
                {open ? "Hide" : "Show"}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="rounded-xl">
                {count}
              </Badge>
              <span className="text-muted-foreground">{open ? "▾" : "▸"}</span>
            </div>
          </CardTitle>
        </CardHeader>
      </button>

      {open ? <CardContent className="space-y-3">{children}</CardContent> : null}
    </Card>
  );
}

export default function ApprovalsPage() {
  const [mounted, setMounted] = useState(false);

  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [role, setRole] = useState<string>("viewer");
  const canAct = role === "admin" || role === "approver";

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;
    setRole(localStorage.getItem("mm_role") || "viewer");
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted]);

  async function loadAll() {
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet("/mailmind/approvals?limit=200");
      setItems(data.items || []);
    } catch (e: any) {
      setErr(e?.message || "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }

  async function handleSyncUnread() {
    setErr(null);
    setSyncing(true);
    try {
      const data = await apiPostQuery("/mailmind/sync-unread", { limit: 10 });
      await loadAll();
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
      await loadAll();
    } catch (e: any) {
      setErr(e?.message || "Approve failed");
    }
  }

  async function executeAction(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/send`);
      await loadAll();
    } catch (e: any) {
      setErr(e?.message || "Execute action failed");
    }
  }

  async function reply(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/reply`);
      await loadAll();
    } catch (e: any) {
      setErr(e?.message || "Reply failed");
    }
  }

  async function noReply(id: number) {
    setErr(null);
    try {
      await apiPost(`/mailmind/approvals/${id}/no-reply`);
      await loadAll();
    } catch (e: any) {
      setErr(e?.message || "No-reply failed");
    }
  }

  const grouped = useMemo(() => {
    const statusOf = (x: Approval) => (x.status || "").toLowerCase();
    const actionOf = (x: Approval) => (x.action_type || "").toLowerCase().trim();
    const hasRealAction = (x: Approval) => {
      const action = actionOf(x);
      return !!action && action !== "none";
    };

    const pending = items.filter((x) => statusOf(x) === "pending");
    const approved = items.filter((x) => statusOf(x) === "approved");

    // Action executed if:
    // - backend explicitly says executed
    // - OR it was sent and had a real action attached
    const executed = items.filter(
      (x) => statusOf(x) === "executed" || (statusOf(x) === "sent" && hasRealAction(x))
    );

    // Pure replies: sent items with no action
    const sent = items.filter(
      (x) => statusOf(x) === "sent" && !hasRealAction(x)
    );

    const no_reply = items.filter((x) => statusOf(x) === "no_reply");
    const rejected = items.filter((x) => statusOf(x) === "rejected");

    const knownIds = new Set([
      ...pending.map((x) => x.id),
      ...approved.map((x) => x.id),
      ...executed.map((x) => x.id),
      ...sent.map((x) => x.id),
      ...no_reply.map((x) => x.id),
      ...rejected.map((x) => x.id),
    ]);

    const other = items.filter((x) => !knownIds.has(x.id));

    return { pending, approved, executed, sent, no_reply, rejected, other };
  }, [items]);

  function ApprovalCard(a: Approval) {
    const status = (a.status || "").toLowerCase();
    const action = (a.action_type || "").toLowerCase().trim();
    const hasRealAction = !!action && action !== "none";

    return (
      <div key={a.id} className="rounded-2xl border p-4">
        <div className="flex flex-col justify-between gap-2 md:flex-row md:items-start">
          <div className="space-y-1">
            <div className="text-sm font-medium">{a.subject || "(No subject)"}</div>
            <div className="text-xs text-muted-foreground">{a.from || ""}</div>

            <div className="mt-2 flex flex-wrap gap-2">
              <StatusBadge status={a.status} />
              {a.action_type ? (
                <Badge className="rounded-xl" variant="secondary">
                  {a.action_type}
                </Badge>
              ) : null}
            </div>
          </div>

          {canAct ? (
            <div className="flex flex-wrap gap-2">
              {status === "pending" ? (
                <Button className="rounded-xl" onClick={() => approve(a.id)}>
                  Approve
                </Button>
              ) : null}

              {(status === "approved" || status === "executed") ? (
                <>
                  <Button className="rounded-xl" variant="secondary" onClick={() => executeAction(a.id)}>
                    Execute Action
                  </Button>
                  <Button className="rounded-xl" variant="secondary" onClick={() => reply(a.id)}>
                    Reply
                  </Button>
                  <Button className="rounded-xl" variant="secondary" onClick={() => noReply(a.id)}>
                    No reply
                  </Button>
                </>
              ) : null}

              {status === "sent" && hasRealAction ? (
                <Badge variant="secondary" className="rounded-xl">
                  Action executed
                </Badge>
              ) : null}

              {status === "sent" && !hasRealAction ? (
                <Badge variant="secondary" className="rounded-xl">
                  Replied
                </Badge>
              ) : null}

              {status === "no_reply" ? (
                <Badge variant="secondary" className="rounded-xl">
                  No reply
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
  }

  if (!mounted) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Approvals</div>
          <div className="text-sm text-muted-foreground">
            Review what Replynto plans to do before it executes.
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

          <Button variant="secondary" className="rounded-xl" onClick={loadAll}>
            Refresh
          </Button>
        </div>
      </div>

      {err ? (
        <div className="rounded-xl border p-3 text-sm text-red-600 whitespace-pre-wrap">{err}</div>
      ) : null}

      {loading ? (
        <div className="text-sm text-muted-foreground">Loading…</div>
      ) : (
        <div className="space-y-4">
          <Section title="Pending approvals" count={grouped.pending.length} defaultOpen>
            {grouped.pending.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No pending approvals. Click <span className="font-medium">Sync Unread</span>.
              </div>
            ) : (
              grouped.pending.map(ApprovalCard)
            )}
          </Section>

          <Section title="Approved (ready)" count={grouped.approved.length}>
            {grouped.approved.length === 0 ? (
              <div className="text-sm text-muted-foreground">No approved items.</div>
            ) : (
              grouped.approved.map(ApprovalCard)
            )}
          </Section>

          <Section title="Executed (action done)" count={grouped.executed.length}>
            {grouped.executed.length === 0 ? (
              <div className="text-sm text-muted-foreground">No executed items.</div>
            ) : (
              grouped.executed.map(ApprovalCard)
            )}
          </Section>

          <Section title="Replied (sent)" count={grouped.sent.length}>
            {grouped.sent.length === 0 ? (
              <div className="text-sm text-muted-foreground">No replies sent yet.</div>
            ) : (
              grouped.sent.map(ApprovalCard)
            )}
          </Section>

          <Section title="No reply" count={grouped.no_reply.length}>
            {grouped.no_reply.length === 0 ? (
              <div className="text-sm text-muted-foreground">None marked as no-reply.</div>
            ) : (
              grouped.no_reply.map(ApprovalCard)
            )}
          </Section>

          <Section title="Rejected" count={grouped.rejected.length}>
            {grouped.rejected.length === 0 ? (
              <div className="text-sm text-muted-foreground">No rejected approvals.</div>
            ) : (
              grouped.rejected.map(ApprovalCard)
            )}
          </Section>

          {grouped.other.length ? (
            <Section title="Other" count={grouped.other.length}>
              {grouped.other.map(ApprovalCard)}
            </Section>
          ) : null}
        </div>
      )}
    </div>
  );
}