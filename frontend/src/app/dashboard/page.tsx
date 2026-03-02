"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Stats = {
  pending: number;
  approved: number;
  sent: number;
};

type GoogleStatus = {
  connected: boolean;
  email: string | null;
};

export default function DashboardHome() {
  const [mounted, setMounted] = useState(false);

  const [stats, setStats] = useState<Stats | null>(null);
  const [g, setG] = useState<GoogleStatus | null>(null);

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const [s, gs] = await Promise.all([
        apiGet("/mailmind/stats"),
        apiGet("/integrations/google/status"),
      ]);
      setStats(s);
      setG(gs);
    } catch (e: any) {
      setErr(e?.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!mounted) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted]);

  if (!mounted) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  const connectedBadge = g?.connected
    ? g.email
      ? `Connected: ${g.email}`
      : "Connected: Google"
    : "Not connected";

  return (
    <div className="space-y-4">
      <div className="flex flex-col justify-between gap-2 md:flex-row md:items-end">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Overview</div>
          <div className="text-sm text-muted-foreground">
            A quick snapshot of what MailMind is doing for your workspace.
          </div>
        </div>

        <Badge
          variant={g?.connected ? "secondary" : "outline"}
          className="w-fit rounded-xl"
        >
          {connectedBadge}
        </Badge>
      </div>

      {err ? (
        <div className="rounded-xl border p-3 text-sm text-red-600 whitespace-pre-wrap">
          {err}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Pending approvals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {loading ? "…" : stats?.pending ?? 0}
            </div>
            <div className="mt-1 text-xs text-muted-foreground">Need human review</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Approved (waiting to send)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {loading ? "…" : stats?.approved ?? 0}
            </div>
            <div className="mt-1 text-xs text-muted-foreground">Ready to execute</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Sent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {loading ? "…" : stats?.sent ?? 0}
            </div>
            <div className="mt-1 text-xs text-muted-foreground">Replies executed</div>
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle>What MailMind does</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          MailMind reviews unread emails, drafts replies, detects actionable intents (like scheduling),
          queues items for approval, executes approved actions, and logs everything for audit.
        </CardContent>
      </Card>
    </div>
  );
}