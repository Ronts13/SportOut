import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { fetchMatches, joinMatch, leaveMatch, getMyPlayer } from "@/lib/api";
import { SPORT_EMOJI } from "@/data/mock";
import { Plus, Users, Clock } from "lucide-react";
import { toast } from "sonner";
import { CreateMatchOverlay } from "@/components/overlays/CreateMatchOverlay";
import { MatchDetailOverlay } from "@/components/overlays/MatchDetailOverlay";

export const Route = createFileRoute("/matches")({
  head: () => ({
    meta: [
      { title: "Matches — SportOut" },
      { name: "description", content: "Find open matches and create your own lobby." },
    ],
  }),
  component: MatchesPage,
});

function MatchesPage() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [openMatch, setOpenMatch] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("All");
  const { data: matches = [], isLoading } = useQuery({ queryKey: ["matches"], queryFn: fetchMatches });
  const { data: me } = useQuery({ queryKey: ["my-player"], queryFn: getMyPlayer });

  const join = useMutation({
    mutationFn: joinMatch,
    onSuccess: () => { toast.success("Joined match"); qc.invalidateQueries({ queryKey: ["matches"] }); },
    onError: (e: any) => toast.error(e?.message ?? "Could not join"),
  });
  const leave = useMutation({
    mutationFn: leaveMatch,
    onSuccess: () => { toast.success("Left match"); qc.invalidateQueries({ queryKey: ["matches"] }); },
    onError: (e: any) => toast.error(e?.message ?? "Could not leave"),
  });

  const sports = ["All", ...Object.keys(SPORT_EMOJI)];
  const visible = filter === "All" ? matches : matches.filter((m) => m.sport === filter);

  return (
    <AppShell title="Matches">
      <div className="px-4 lg:px-8 mt-4">
        <div className="flex items-center justify-between mb-4 px-1">
          <h2 className="text-base font-semibold text-white/90">Open Matches</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow text-xs font-bold hover:bg-teal-glow/25 transition-colors active:scale-95"
          >
            <Plus className="w-3.5 h-3.5" /> Create Match
          </button>
        </div>

        <div className="flex gap-2 overflow-x-auto no-scrollbar mb-4">
          {sports.map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`sport-chip ${filter === s ? "active" : ""}`}
            >
              {s === "All" ? "All Sports" : `${SPORT_EMOJI[s] ?? ""} ${s}`}
            </button>
          ))}
        </div>

        {isLoading && <p className="text-white/40 text-sm px-1">Loading matches…</p>}
        {!isLoading && visible.length === 0 && (
          <p className="text-white/40 text-sm px-1">No upcoming matches — be the first to create one.</p>
        )}

        <div className="flex flex-col lg:grid lg:grid-cols-2 gap-3 pb-6">
          {visible.map((m) => {
            const emoji = SPORT_EMOJI[m.sport] ?? "🎯";
            const joined = me ? m.rosters.some((r) => r.player?.id === me.id) : false;
            const missing = Math.max(0, m.max_players - m.rosters.length);
            const time = new Date(m.scheduled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            return (
              <div
                key={m.id}
                onClick={() => setOpenMatch(m.id)}
                className="rounded-2xl bg-navy-800 border border-white/5 p-4 shadow-card hover:border-teal-glow/30 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-teal-glow/10 border border-teal-glow/20 flex items-center justify-center text-lg flex-shrink-0">
                      {emoji}
                    </div>
                    <div className="min-w-0">
                      <p className="text-white font-bold text-sm leading-tight truncate">{m.sport} · {m.format}</p>
                      <p className="text-white/40 text-xs mt-0.5 truncate">{m.facility?.name ?? m.court?.name ?? "TBD"}</p>
                    </div>
                  </div>
                  <span className="text-white/60 text-xs font-mono flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {time}
                  </span>
                </div>

                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="text-teal-glow font-semibold flex items-center gap-1">
                    <Users className="w-3.5 h-3.5" />
                    {missing === 0 ? "Full" : `${missing} needed`}
                  </span>
                  <span className="text-white/40">{m.rosters.length}/{m.max_players} joined</span>
                </div>

                <div className="flex items-center justify-between" onClick={(e) => e.stopPropagation()}>
                  <div className="flex -space-x-2">
                    {m.rosters.slice(0, 4).map((r) => (
                      <div key={r.id} className="w-8 h-8 rounded-full bg-navy-700 border-2 border-navy-800 flex items-center justify-center text-xs font-bold text-teal-glow" title={r.player?.display_name ?? ""}>
                        {(r.player?.display_name ?? "?").charAt(0).toUpperCase()}
                      </div>
                    ))}
                    {m.rosters.length > 4 && (
                      <div className="w-8 h-8 rounded-full bg-navy-700 border-2 border-navy-800 flex items-center justify-center text-[10px] font-bold text-white/60">
                        +{m.rosters.length - 4}
                      </div>
                    )}
                  </div>
                  {joined ? (
                    <button
                      onClick={() => leave.mutate(m.id)}
                      disabled={leave.isPending}
                      className="px-4 py-1.5 rounded-xl bg-white/5 border border-white/10 text-white/70 text-xs font-semibold hover:bg-white/10 transition-colors"
                    >
                      Leave
                    </button>
                  ) : (
                    <button
                      onClick={() => join.mutate(m.id)}
                      disabled={join.isPending || missing === 0}
                      className="px-4 py-1.5 rounded-xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow text-xs font-semibold hover:bg-teal-glow/25 transition-colors disabled:opacity-50"
                    >
                      Join
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <CreateMatchOverlay open={showCreate} onClose={() => setShowCreate(false)} />
      <MatchDetailOverlay matchId={openMatch} onClose={() => setOpenMatch(null)} />
    </AppShell>
  );
}
