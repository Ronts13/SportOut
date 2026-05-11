import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { CourtsMap, type MapCourt } from "@/components/CourtsMap";
import { fetchCourts, type DbCourt } from "@/lib/api";
import { Search, ChevronRight } from "lucide-react";
import { CourtDetailOverlay } from "@/components/overlays/CourtDetailOverlay";

export const Route = createFileRoute("/courts")({
  head: () => ({
    meta: [
      { title: "Courts — SportOut" },
      { name: "description", content: "Find sports courts near you on the live map." },
    ],
  }),
  component: CourtsPage,
});

function CourtsPage() {
  const [q, setQ] = useState("");
  const [openCourt, setOpenCourt] = useState<string | null>(null);
  const { data: courts = [], isLoading } = useQuery({ queryKey: ["courts"], queryFn: fetchCourts });

  const filtered = courts.filter((c: DbCourt) => c.name.toLowerCase().includes(q.toLowerCase()) || (c.facility?.name ?? "").toLowerCase().includes(q.toLowerCase()));
  const live = courts.filter((c) => c.current_occupancy > 0).length;

  const mapCourts: MapCourt[] = courts.flatMap((c) => {
    const lat = c.facility?.latitude;
    const lng = c.facility?.longitude;
    if (typeof lat !== "number" || typeof lng !== "number") return [];
    return [{ id: c.id, name: c.facility?.name ?? c.name, lat, lng, live: c.current_occupancy > 0 }];
  });

  return (
    <AppShell title="Courts">
      <div className="px-4 lg:px-8 mt-4">
        <div className="relative mb-5">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search courts…"
            className="w-full bg-navy-800 border border-white/10 rounded-2xl pl-10 pr-4 py-3 text-sm text-white/80 placeholder-white/25 outline-none focus:border-teal-glow/40 transition-colors"
          />
        </div>

        <div className="relative w-full h-40 lg:h-64 rounded-2xl overflow-hidden bg-navy-800 border border-teal-glow/15 shadow-card mb-5">
          <CourtsMap interactive={true} courts={mapCourts} onCourtClick={(id) => setOpenCourt(String(id))} />
        </div>

        <div className="flex items-center justify-between mb-3 px-1">
          <h2 className="text-base font-semibold text-white/90">Nearby Courts</h2>
          <span className="text-xs text-white/30">{live} live</span>
        </div>

        {isLoading && <p className="text-white/40 text-sm px-1">Loading courts…</p>}

        <div className="flex flex-col lg:grid lg:grid-cols-2 gap-3 pb-6">
          {filtered.map((c) => {
            const isLive = c.current_occupancy > 0;
            return (
              <button
                key={c.id}
                onClick={() => setOpenCourt(c.id)}
                className="flex items-center gap-4 w-full rounded-2xl bg-navy-800 border border-white/5 p-4 cursor-pointer hover:border-teal-glow/30 active:scale-[0.98] transition-all shadow-card text-left"
              >
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    isLive ? "bg-teal-glow/10 border border-teal-glow/20" : "bg-navy-700 border border-white/10"
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${isLive ? "bg-teal-glow live-dot" : "bg-teal-dim/60"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-semibold text-sm truncate">{c.facility?.name ?? c.name}</p>
                  <p className="text-white/40 text-xs mt-0.5 truncate">
                    {c.sport} · {c.current_occupancy}/{c.max_capacity} players · {c.facility?.address_city ?? ""}
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-white/20 flex-shrink-0" />
              </button>
            );
          })}
        </div>
      </div>

      <CourtDetailOverlay courtId={openCourt} onClose={() => setOpenCourt(null)} />
    </AppShell>
  );
}
