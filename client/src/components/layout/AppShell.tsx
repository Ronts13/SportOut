import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import { Home, MapPin, Zap, BarChart3, User, Bell, LogOut } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useQuery } from "@tanstack/react-query";
import { getMyProfile } from "@/lib/api";

const TABS = [
  { to: "/",         label: "Feed",     icon: Home },
  { to: "/courts",   label: "Courts",   icon: MapPin },
  { to: "/matches",  label: "Matches",  icon: Zap },
  { to: "/rankings", label: "Rankings", icon: BarChart3 },
  { to: "/profile",  label: "Profile",  icon: User },
] as const;

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-xl bg-teal-base/20 border border-teal-glow/40 flex items-center justify-center shadow-teal-glow-sm">
        <span className="text-teal-glow font-extrabold text-sm leading-none tracking-tight">S</span>
      </div>
      <span className="text-foreground font-bold text-xl tracking-tight">SportOut</span>
    </div>
  );
}

export function AppShell({ children, title }: { children: ReactNode; title: string }) {
  const path = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (to: string) => (to === "/" ? path === "/" : path.startsWith(to));
  const { session, loading, signOut } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !session) navigate({ to: "/auth" });
  }, [loading, session, navigate]);

  const { data: profile } = useQuery({
    queryKey: ["my-profile", session?.user.id],
    queryFn: getMyProfile,
    enabled: !!session,
  });

  const initial = (profile?.display_name ?? session?.user.email ?? "?").charAt(0).toUpperCase();
  const name = profile?.display_name || session?.user.email?.split("@")[0] || "Player";

  const handleSignOut = () => {
    signOut();
    navigate({ to: "/auth" });
  };

  return (
    <div className="min-h-[100dvh] bg-navy-950 text-foreground overflow-x-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col bg-navy-900/95 border-r border-white/5 backdrop-blur-md z-50">
        <div className="px-6 pt-8 pb-6"><Logo /></div>
        <nav className="flex-1 px-3 flex flex-col gap-1">
          {TABS.map(({ to, label, icon: Icon }) => {
            const active = isActive(to);
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 w-full px-3 py-3 rounded-xl transition-all duration-200 ${
                  active ? "bg-teal-glow/10 border border-teal-glow/30" : "hover:bg-white/5 border border-transparent"
                }`}
              >
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${active ? "bg-teal-glow/15" : ""}`}>
                  <Icon className={`w-5 h-5 ${active ? "text-teal-glow" : "text-white/40"}`} />
                </div>
                <span className={`text-sm font-medium ${active ? "text-teal-glow" : "text-white/45"}`}>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-white/5 px-4 py-5 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-navy-700 border-2 border-teal-glow/40 flex items-center justify-center flex-shrink-0">
            <span className="text-teal-glow font-bold text-sm">{initial}</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-foreground text-sm font-semibold truncate">{name}</p>
            <p className="text-teal-glow/70 text-xs font-medium truncate">{profile?.handle ? `@${profile.handle}` : "Player"}</p>
          </div>
          <button onClick={handleSignOut} title="Sign out" className="text-white/40 hover:text-teal-glow transition">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-col min-h-[100dvh] lg:ml-64 safe-pb-main lg:pb-8">
        <header className="sticky top-0 z-40 px-5 safe-pt lg:pt-5 pb-3 flex items-center justify-between bg-gradient-to-b from-navy-950 via-navy-950/95 to-transparent">
          <div className="lg:hidden"><Logo /></div>
          <h1 className="hidden lg:block text-foreground font-bold text-xl tracking-tight">{title}</h1>
          <div className="flex items-center gap-3">
            <button className="relative w-9 h-9 rounded-full bg-navy-700/80 border border-white/5 flex items-center justify-center hover:border-teal-glow/40 transition-colors">
              <Bell className="w-4 h-4 text-white/70" />
              <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-teal-glow live-dot" />
            </button>
          </div>
        </header>

        <main className="flex-1 section-enter">{children}</main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-gradient-to-t from-navy-950 via-navy-950/98 to-transparent border-t border-white/5 backdrop-blur-md z-50 safe-pb-nav">
        <div className="flex items-center justify-around px-2 py-3">
          {TABS.map(({ to, label, icon: Icon }) => {
            const active = isActive(to);
            return (
              <Link key={to} to={to} className="flex flex-col items-center gap-1">
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-all ${active ? "bg-teal-glow/15 border border-teal-glow/30" : ""}`}>
                  <Icon className={`w-5 h-5 ${active ? "text-teal-glow" : "text-white/40"}`} />
                </div>
                <span className={`text-[10px] ${active ? "text-teal-glow font-semibold" : "text-white/40"}`}>{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
