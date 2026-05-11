import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { CourtsMap, type MapCourt } from "@/components/CourtsMap";
import { fetchCourts } from "@/lib/api";
import { Play, MapPin, Star, Maximize2 } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SportOut — Find courts, matches & players" },
      { name: "description", content: "Live sports feed: courts, matches and players in your area." },
      { property: "og:title", content: "SportOut — Find courts, matches & players" },
    ],
  }),
  component: FeedPage,
});

function FeedPage() {
  const { data: courts = [] } = useQuery({ queryKey: ["courts"], queryFn: fetchCourts });
  const liveCourts = courts.filter((c) => c.current_occupancy > 0).length;
  const mapCourts: MapCourt[] = courts.flatMap((c) => {
    const lat = c.facility?.latitude;
    const lng = c.facility?.longitude;
    if (typeof lat !== "number" || typeof lng !== "number") return [];
    return [{ id: c.id, name: c.facility?.name ?? c.name, lat, lng, live: c.current_occupancy > 0 }];
  });
  return (
    <AppShell title="Feed">
      {/* Highlights */}
      <section className="px-4 lg:px-8 mt-2">
        <SectionHeader title="Highlights" cta="See all" />
        <div className="relative w-full aspect-video rounded-2xl overflow-hidden bg-navy-800 shadow-card border border-white/5 group cursor-pointer active:scale-[0.98] transition-transform duration-150">
          <div className="absolute inset-0 bg-gradient-to-br from-navy-700 via-navy-800 to-navy-950" />
          <div
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage:
                "linear-gradient(rgba(0,255,231,.15) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,231,.15) 1px, transparent 1px)",
              backgroundSize: "32px 32px",
            }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 rounded-full bg-teal-glow/5 border border-teal-glow/20 flex items-center justify-center shadow-teal-glow group-hover:bg-teal-glow/10 transition-colors">
              <Play className="w-10 h-10 text-teal-glow/70 group-hover:text-teal-glow transition-colors" />
            </div>
          </div>
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-4">
            <div className="flex items-end justify-between">
              <div>
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-teal-glow/15 border border-teal-glow/40 mb-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-glow live-dot" />
                  <span className="text-teal-glow text-[10px] font-bold uppercase tracking-widest">Live</span>
                </span>
                <p className="text-white font-bold text-sm leading-tight">May Highlights</p>
                <p className="text-white/50 text-xs mt-0.5 flex items-center gap-1">
                  <MapPin className="w-3 h-3" /> Sportek Tel Aviv
                </p>
              </div>
              <span className="text-xs text-white/60 bg-black/50 px-2 py-1 rounded-lg font-mono">2:34</span>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-3 overflow-x-auto no-scrollbar pb-1 lg:grid lg:grid-cols-4 lg:overflow-x-visible">
          {["1:12", "0:58", "3:07", "2:20"].map((d) => (
            <div key={d} className="flex-shrink-0 w-28 lg:w-auto aspect-video rounded-xl bg-navy-800 border border-white/5 shadow-card cursor-pointer hover:border-teal-glow/30 active:scale-95 transition-all relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-navy-700 to-navy-900" />
              <div className="absolute bottom-1.5 left-1.5 text-[10px] text-white/50 font-mono">{d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Map */}
      <section className="px-4 lg:px-8 mt-6">
        <SectionHeader title="Live Courts" cta="Add" />
        <div className="relative w-full h-52 lg:h-72 rounded-2xl overflow-hidden bg-navy-800 shadow-card border border-teal-glow/15 group cursor-pointer">
          <div className="absolute inset-0"><CourtsMap interactive={false} courts={mapCourts} /></div>
          <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-navy-950/80 border border-teal-glow/25 rounded-xl px-3 py-1.5 shadow-teal-glow-sm backdrop-blur-sm z-[400]">
            <span className="w-2 h-2 rounded-full bg-teal-glow live-dot" />
            <span className="text-xs font-semibold text-white/80">{liveCourts} Courts Live</span>
          </div>
          <div className="absolute top-3 right-3 z-[400] flex items-center gap-1 bg-navy-950/70 border border-white/10 rounded-lg px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Maximize2 className="w-3 h-3 text-white/60" />
            <span className="text-white/60 text-[10px] font-medium">Expand</span>
          </div>
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent px-4 py-3 z-[400] pointer-events-none">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-white font-semibold text-sm leading-tight">Tel Aviv Sports Zone</p>
                <p className="text-white/45 text-xs mt-0.5">Hayarkon Park District · 1.2 km away</p>
              </div>
              <div className="flex items-center gap-1 bg-navy-950/70 border border-teal-glow/30 rounded-lg px-2 py-1">
                <Star className="w-3 h-3 text-teal-glow fill-teal-glow" />
                <span className="text-teal-glow text-xs font-bold">1.2k</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick stats */}
      <section className="px-4 lg:px-8 mt-6">
        <SectionHeader title="Leaderboard" cta="Full Table" />
        <div className="flex gap-3 overflow-x-auto no-scrollbar pb-1 lg:grid lg:grid-cols-3 lg:overflow-x-visible">
          <StatCard value="8.0k" label="Total Players" />
          <StatCard value={`${courts.length}`} label="Active Courts" />
          <StatCard value="94%" label="Match Rate" />
        </div>
      </section>
    </AppShell>
  );
}

function SectionHeader({ title, cta }: { title: string; cta: string }) {
  return (
    <div className="flex items-center justify-between mb-3 px-1">
      <h2 className="text-base font-semibold text-white/90 tracking-tight">{title}</h2>
      <button className="text-xs text-teal-glow font-medium hover:text-teal-base transition-colors">{cta}</button>
    </div>
  );
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex-shrink-0 w-36 lg:w-auto rounded-2xl border border-white/5 bg-navy-800 p-4 shadow-card">
      <p className="text-teal-glow text-2xl font-extrabold tracking-tight">{value}</p>
      <p className="text-white/50 text-xs mt-1 font-medium">{label}</p>
    </div>
  );
}
