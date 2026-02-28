import Link from "next/link";
import { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { LayoutDashboard, Mail, ScrollText, Settings, LogOut } from "lucide-react";

const NavItem = ({
  href,
  icon,
  label,
  badge,
}: {
  href: string;
  icon: ReactNode;
  label: string;
  badge?: string;
}) => {
  return (
    <Link
      href={href}
      className="flex items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm transition hover:bg-muted"
    >
      <div className="flex items-center gap-3">
        <span className="text-muted-foreground">{icon}</span>
        <span className="font-medium">{label}</span>
      </div>
      {badge ? <Badge variant="secondary">{badge}</Badge> : null}
    </Link>
  );
};

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 p-4 md:grid-cols-[260px_1fr] md:p-8">
        {/* Sidebar */}
        <aside className="rounded-2xl border bg-card p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-semibold leading-tight">MailMind</div>
              <div className="text-xs text-muted-foreground">Ops Dashboard</div>
            </div>
            <Badge className="rounded-xl">Beta</Badge>
          </div>

          <Separator className="my-4" />

          <nav className="space-y-1">
            <NavItem href="/dashboard" icon={<LayoutDashboard size={18} />} label="Overview" />
            <NavItem href="/dashboard/approvals" icon={<Mail size={18} />} label="Approvals" badge="New" />
            <NavItem href="/dashboard/audit" icon={<ScrollText size={18} />} label="Audit Log" />
            <NavItem href="/dashboard/settings" icon={<Settings size={18} />} label="Settings" />
          </nav>

          <Separator className="my-4" />

          <Link
            href="/login"
            className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground"
          >
            <LogOut size={18} />
            Logout
          </Link>

          <div className="mt-4 rounded-xl bg-muted/40 p-3 text-xs text-muted-foreground">
            <div className="font-medium text-foreground">Workspace</div>
            <div className="mt-1">DemoCompany</div>
            <div className="mt-2">Mode: Approval-first</div>
          </div>
        </aside>

        {/* Main */}
        <main className="space-y-4">
          {children}
          <div className="pb-8 text-center text-xs text-muted-foreground">
            © {new Date().getFullYear()} MailMind — Automate email & tasks safely.
          </div>
        </main>
      </div>
    </div>
  );
}