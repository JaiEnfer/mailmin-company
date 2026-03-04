"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function DashboardHome() {
  const [stats, setStats] = useState<any>(null);
  const [google, setGoogle] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const s = await apiGet("/mailmind/stats");
        setStats(s);
      } catch {}
      try {
        const g = await apiGet("/integrations/google/status");
        setGoogle(g);
      } catch {}
    })();
  }, []);

  const connected = google?.connected ? `Connected: ${google?.email || "Google"}` : "Not connected";

  return (
    <div className="space-y-4">
      <div className="flex flex-col justify-between gap-2 md:flex-row md:items-end">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Overview</div>
          <div className="text-sm text-muted-foreground">
            A quick snapshot of what MailMind is doing for your workspace.
          </div>
        </div>
        <Badge variant="secondary" className="w-fit rounded-xl">
          {connected}
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Pending approvals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.pending ?? "—"}</div>
            <div className="mt-1 text-xs text-muted-foreground">Need human review</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Executed actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.executed ?? "—"}</div>
            <div className="mt-1 text-xs text-muted-foreground">Tasks completed</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Replies sent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.sent ?? "—"}</div>
            <div className="mt-1 text-xs text-muted-foreground">Email replies sent</div>
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle>What MailMind does</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Sync unread emails → draft replies → detect actions → queue approvals → execute approved actions and log everything.
        </CardContent>
      </Card>
    </div>
  );
}