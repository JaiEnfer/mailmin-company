"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

type AuditItem = {
  id: number;
  action: string;
  details: any;
  created_at?: string | null;
};

export default function AuditPage() {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet("/audit?limit=50");
      setItems(data.items || []);
    } catch (e: any) {
      setErr(e.message || "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Audit Log</div>
          <div className="text-sm text-muted-foreground">
            A tamper-evident history of what MailMind suggested and executed.
          </div>
        </div>
        <Button variant="secondary" className="rounded-xl" onClick={load}>
          Refresh
        </Button>
      </div>

      {err ? <div className="rounded-xl border p-3 text-sm text-red-600">{err}</div> : null}

      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Recent events
            <Badge variant="secondary" className="rounded-xl">{items.length}</Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          {loading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}
          {!loading && items.length === 0 ? (
            <div className="text-sm text-muted-foreground">No audit events yet.</div>
          ) : null}

          {items.map((a) => (
            <div key={a.id} className="rounded-2xl border p-4">
              <div className="flex flex-col justify-between gap-2 md:flex-row md:items-center">
                <div className="space-y-1">
                  <div className="text-sm font-medium">{a.action}</div>
                  <div className="text-xs text-muted-foreground">{a.created_at || ""}</div>
                </div>
                <Badge className="rounded-xl" variant="outline">#{a.id}</Badge>
              </div>

              <Separator className="my-3" />

              <pre className="whitespace-pre-wrap rounded-xl bg-muted/40 p-3 text-xs">
                {JSON.stringify(a.details, null, 2)}
              </pre>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}