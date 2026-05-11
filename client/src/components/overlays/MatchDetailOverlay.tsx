import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cancelMatch, fetchMatchDetail, getMyPlayer, joinMatch, leaveMatch } from "@/lib/api";
import { OverlaySheet } from "./Sheet";
import { PlayerDetailOverlay } from "./PlayerDetailOverlay";
import { useAuth } from "@/hooks/use-auth";
import { Clock, Users } from "lucide-react";
import { toast } from "sonner";

export function MatchDetailOverlay({ matchId, onClose }: { matchId: string | null; onClose: () => void }) {
  const open = !!matchId;
  const qc = useQueryClient();
  const { session } = useAuth();
  const [pickedPlayer, setPickedPlayer] = useState<string | null>(null);

  const { data: match } = useQuery({
    queryKey: ["match-detail", matchId],
    queryFn: () => fetchMatchDetail(matchId!),
    enabled: open,
  });
  const { data: me } = useQuery({ queryKey: ["my-player"], queryFn: getMyPlayer, enabled: open });

  const join = useMutation({
    mutationFn: () => joinMatch(matchId!),
    onSuccess: () => {
      toast.success("Joined");
      qc.invalidateQueries();
    },
    onError: (e: any) => toast.error(e?.message ?? "Failed"),
  });
  const leave = useMutation({
    mutationFn: () => leaveMatch(matchId!),
    onSuccess: () => {
      toast.success("Left");
      qc.invalidateQueries();
    },
    onError: (e: any) => toast.error(e?.message ?? "Failed"),
  });
  const cancel = useMutation({
    mutationFn: () => cancelMatch(matchId!),
    onSuccess: () => {
      toast.success("Match cancelled");
      qc.invalidateQueries();
      onClose();
    },
    onError: (e: any) => toast.error(e?.message ?? "Failed"),
  });

  const isCreator = session?.user.id === match?.created_by;
  const joined = !!match?.rosters.some((r) => r.player?.id === me?.id);
  const time = match ? new Date(match.scheduled_at).toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" }) : "";
  const missing = match ? Math.max(0, match.max_players - match.rosters.length) : 0;

  return (
    <>
      <OverlaySheet open={open} onClose={onClose} title={match ? `${match.sport} · ${match.format}` : "Match"}>
        {!match ? (
          <div className="p-6 text-white/50 text-sm">Loading…</div>
        ) : (
          <div className="p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-white/60 flex items-center gap-1.5">
                <Clock className="w-4 h-4" /> {time}
              </span>
              <span className="text-teal-glow font-semibold flex items-center gap-1.5">
                <Users className="w-4 h-4" />
                {missing === 0 ? "Full" : `${missing} needed`}
              </span>
            </div>

            <div className="rounded-xl bg-navy-800 border border-white/5 p-3">
              <p className="text-white/40 text-[10px] uppercase tracking-widest font-semibold mb-1">Court</p>
              <p className="text-white font-semibold text-sm">
                {match.facility?.name ?? match.court?.name ?? "TBD"}
              </p>
              {match.facility?.address_city && (
                <p className="text-white/40 text-xs mt-0.5">{match.facility.address_city}</p>
              )}
            </div>

            {(match.min_rating || match.max_rating) && (
              <p className="text-white/50 text-xs">
                Rating range:{" "}
                <span className="text-teal-glow font-semibold">
                  {match.min_rating ?? "any"} – {match.max_rating ?? "any"}
                </span>
              </p>
            )}

            <div>
              <p className="text-white/35 text-[10px] font-semibold uppercase tracking-widest mb-2">
                Roster ({match.rosters.length}/{match.max_players})
              </p>
              <div className="grid grid-cols-2 gap-2">
                {match.rosters.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => r.player && setPickedPlayer(r.player.id)}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-navy-800 border border-white/5 hover:border-teal-glow/30 transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded-full bg-navy-700 border border-teal-glow/30 flex items-center justify-center text-teal-glow font-bold text-xs flex-shrink-0">
                      {(r.player?.display_name ?? "?").charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-semibold truncate">{r.player?.display_name ?? "?"}</p>
                      <p className="text-white/40 text-[10px]">{r.confirmed ? "Confirmed" : "Invited"}</p>
                    </div>
                  </button>
                ))}
                {Array.from({ length: missing }).map((_, i) => (
                  <div
                    key={`empty-${i}`}
                    className="flex items-center justify-center px-3 py-2.5 rounded-xl border border-dashed border-white/10 text-white/30 text-xs"
                  >
                    Open spot
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              {isCreator ? (
                <button
                  onClick={() => cancel.mutate()}
                  className="flex-1 py-3 rounded-xl bg-destructive/10 border border-destructive/40 text-destructive font-bold text-sm hover:bg-destructive/20 active:scale-[0.98]"
                >
                  Cancel match
                </button>
              ) : joined ? (
                <button
                  onClick={() => leave.mutate()}
                  className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-white/70 font-bold text-sm hover:bg-white/10 active:scale-[0.98]"
                >
                  Leave
                </button>
              ) : (
                <button
                  onClick={() => join.mutate()}
                  disabled={missing === 0}
                  className="flex-1 py-3 rounded-xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow font-bold text-sm hover:bg-teal-glow/25 disabled:opacity-50 active:scale-[0.98]"
                >
                  Join
                </button>
              )}
            </div>
          </div>
        )}
      </OverlaySheet>
      <PlayerDetailOverlay playerId={pickedPlayer} onClose={() => setPickedPlayer(null)} />
    </>
  );
}
