import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { fetchRankings, getFollowedUserIds, type RankedPlayer } from "@/lib/api";
import { PlayerDetailOverlay } from "@/components/overlays/PlayerDetailOverlay";

export const Route = createFileRoute("/rankings")({
  head: () => ({
    meta: [
      { title: "Rankings — SportOut" },
      { name: "description", content: "Top ranked players by sport, region and following." },
    ],
  }),
  component: RankingsPage,
});

const SPORTS = ["All Sports", "Padel", "Tennis", "Football", "Basketball", "Table Tennis", "Footvolley", "Boxing"];
const REGIONS = ["All Cities", "Tel Aviv", "Herzliya", "Ramat Gan", "Jerusalem", "Haifa"];

function RankingsPage() {
  const [sport, setSport] = useState("All Sports");
  const [region, setRegion] = useState("All Cities");
  const [followingOnly, setFollowingOnly] = useState(false);
  const [openPlayer, setOpenPlayer] = useState<string | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ["rankings", sport, region],
    queryFn: () =>
      fetchRankings({
        sport: sport === "All Sports" ? null : sport,
        city: region === "All Cities" ? null : region,
      }),
  });

  const { data: followed = new Set<string>() } = useQuery({
    queryKey: ["my-following-ids"],
    queryFn: getFollowedUserIds,
    enabled: followingOnly,
  });

  const sorted = useMemo(() => {
    let r: RankedPlayer[] = rows;
    if (followingOnly) r = r.filter((p) => followed.has(p.user_id));
    // dedupe by player.id keeping highest rating
    const map = new Map<string, RankedPlayer>();
    for (const p of r) {
      const cur = map.get(p.id);
      if (!cur || p.rating > cur.rating) map.set(p.id, p);
    }
    return Array.from(map.values()).sort((a, b) => b.rating - a.rating);
  }, [rows, followingOnly, followed]);

  const top3 = sorted.slice(0, 3);
  const rest = sorted.slice(3);

  return (
    <AppShell title="Rankings">
      <div className="px-4 lg:px-8 mt-4">
        {/* Sport filter */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 mb-3">
          {SPORTS.map((s) => (
            <button key={s} onClick={() => setSport(s)} className={`sport-chip ${sport === s ? "active" : ""}`}>
              {s}
            </button>
          ))}
        </div>
        {/* Region + following */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 mb-5">
          {REGIONS.map((r) => (
            <button key={r} onClick={() => setRegion(r)} className={`sport-chip ${region === r ? "active" : ""}`}>
              {r === "All Cities" ? "🌍 All Cities" : r}
            </button>
          ))}
          <button
            onClick={() => setFollowingOnly((v) => !v)}
            className={`sport-chip ${followingOnly ? "active" : ""}`}
          >
            👥 Following
          </button>
        </div>

        {/* Podium */}
        <div className="flex items-end justify-center gap-3 mb-6 min-h-[180px]">
          {top3[1] && <PodiumSlot player={top3[1]} place={2} height="h-24" onClick={() => setOpenPlayer(top3[1].id)} />}
          {top3[0] && <PodiumSlot player={top3[0]} place={1} height="h-32" big onClick={() => setOpenPlayer(top3[0].id)} />}
          {top3[2] && <PodiumSlot player={top3[2]} place={3} height="h-20" onClick={() => setOpenPlayer(top3[2].id)} />}
        </div>

        <div className="flex items-center justify-between mb-3 px-1">
          <h2 className="text-base font-semibold text-white/90">Top Players</h2>
          <span className="text-xs text-white/30">Rating</span>
        </div>

        {isLoading && <p className="text-white/40 text-sm px-1">Loading…</p>}

        <div className="flex flex-col gap-2 pb-6">
          {rest.map((p, i) => (
            <button
              key={p.id}
              onClick={() => setOpenPlayer(p.id)}
              className="flex items-center gap-3 p-3 rounded-2xl bg-navy-800 border border-white/5 hover:border-teal-glow/20 transition-colors text-left"
            >
              <span className="w-7 text-center text-white/40 font-mono text-sm">{i + 4}</span>
              <div className="w-10 h-10 rounded-full bg-navy-700 border border-teal-glow/30 flex items-center justify-center text-teal-glow font-bold">
                {(p.display_name || "?").charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-semibold truncate">{p.display_name}</p>
                <p className="text-white/40 text-xs truncate">{p.sport} · {p.home_city ?? "—"}</p>
              </div>
              <span className="text-teal-glow font-extrabold text-lg">{Math.round(p.rating)}</span>
            </button>
          ))}
          {!isLoading && sorted.length === 0 && (
            <p className="text-white/40 text-sm px-1">No players match these filters.</p>
          )}
        </div>
      </div>

      <PlayerDetailOverlay playerId={openPlayer} onClose={() => setOpenPlayer(null)} />
    </AppShell>
  );
}

function PodiumSlot({
  player,
  place,
  height,
  big,
  onClick,
}: {
  player: RankedPlayer;
  place: number;
  height: string;
  big?: boolean;
  onClick: () => void;
}) {
  const medal = place === 1 ? "🥇" : place === 2 ? "🥈" : "🥉";
  return (
    <button onClick={onClick} className="flex flex-col items-center w-24">
      <div className="text-2xl mb-1">{medal}</div>
      <div className={`${big ? "w-16 h-16" : "w-14 h-14"} rounded-full bg-navy-700 border-2 border-teal-glow/40 flex items-center justify-center ${big ? "shadow-teal-glow" : "shadow-teal-glow-sm"} mb-2`}>
        <span className={`text-teal-glow font-extrabold ${big ? "text-xl" : "text-lg"}`}>
          {(player.display_name || "?").charAt(0).toUpperCase()}
        </span>
      </div>
      <p className="text-white text-xs font-semibold text-center truncate w-full">{player.display_name}</p>
      <p className="text-teal-glow text-xs font-bold">{Math.round(player.rating)}</p>
      <div className={`mt-2 ${height} w-full rounded-t-2xl bg-gradient-to-t from-teal-glow/5 to-teal-glow/20 border border-teal-glow/20 border-b-0 flex items-start justify-center pt-2`}>
        <span className="text-teal-glow/70 font-extrabold text-lg">{place}</span>
      </div>
    </button>
  );
}
