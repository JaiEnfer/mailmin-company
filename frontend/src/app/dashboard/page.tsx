import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function DashboardHome() {
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
          Connected: Gmail + Calendar
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Pending approvals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">3</div>
            <div className="mt-1 text-xs text-muted-foreground">Need human review</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Sent today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">2</div>
            <div className="mt-1 text-xs text-muted-foreground">Replies executed</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Tasks executed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">2</div>
            <div className="mt-1 text-xs text-muted-foreground">Calendar events created</div>
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