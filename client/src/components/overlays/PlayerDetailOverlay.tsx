import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchPlayerDetail, follow, isFollowing, unfollow } from "@/lib/api";
import { OverlaySheet } from "./Sheet";
import { toast } from "sonner";

export function PlayerDetailOverlay({ playerId, onClose }: { playerId: string | null; onClose: () => void }) {
  const open = !!playerId;
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["player-detail", playerId],
    queryFn: () => fetchPlayerDetail(playerId!),
    enabled: open,
  });

  const { data: followingNow = false } = useQuery({
    queryKey: ["is-following", data?.player.user_id],
    queryFn: () => isFollowing(data!.player.user_id),
    enabled: !!data?.player.user_id,
  });

  const [activeSport, setActiveSport] = useState<string | null>(null);
  useEffect(() => {
    if (data?.sports.length) setActiveSport(data.sports[0].sport);
  }, [data]);

  const followMut = useMutation({
    mutationFn: async () => {
      if (followingNow) await unfollow(data!.player.user_id);
      else await follow(data!.player.user_id);
    },
    onSuccess: () => {
      toast.success(followingNow ? "Unfollowed" : "Following");
      qc.invalidateQueries({ queryKey: ["is-following"] });
      qc.invalidateQueries({ queryKey: ["player-detail", playerId] });
    },
    onError: (e: any) => toast.error(e?.message ?? "Failed"),
  });

  const sp = data?.sports.find((s: any) => s.sport === activeSport) ?? data?.sports[0];

  return (
    <OverlaySheet open={open} onClose={onClose} title={data?.profile?.display_name || data?.player.display_name || "Player"}>
      {isLoading || !data ? (
        <div className="p-6 text-white/50 text-sm">Loading…</div>
      ) : (
        <div className="p-5 flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-navy-700 border-2 border-teal-glow/50 shadow-teal-glow flex items-center justify-center">
              <span className="text-teal-glow text-2xl font-extrabold">
                {(data.profile?.display_name ?? data.player.display_name ?? "?").charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-base truncate">{data.profile?.display_name ?? data.player.display_name}</p>
              {data.profile?.handle && <p className="text-teal-glow/80 text-xs">@{data.profile.handle}</p>}
              <p className="text-white/40 text-xs mt-0.5 truncate">
                {data.player.home_city ?? "—"} · {(data.player.preferred_sports ?? []).join(", ")}
              </p>
            </div>
          </div>

          {(data.player.bio || data.profile?.bio) && (
            <p className="text-white/70 text-sm leading-snug">{data.profile?.bio ?? data.player.bio}</p>
          )}

          <div className="grid grid-cols-3 gap-2">
            <Stat value={(sp?.rating ?? 0).toFixed(0)} label="Rating" accent />
            <Stat value={`${data.followers}`} label="Followers" />
            <Stat value={`${data.following}`} label="Following" />
          </div>

          {data.sports.length > 0 && (
            <div className="flex gap-2 overflow-x-auto no-scrollbar">
              {data.sports.map((s: any) => (
                <button
                  key={s.sport}
                  onClick={() => setActiveSport(s.sport)}
                  className={`sport-chip ${activeSport === s.sport ? "active" : ""}`}
                >
                  {s.sport}
                </button>
              ))}
            </div>
          )}

          {sp && (
            <div className="grid grid-cols-3 gap-2">
              <Stat value={`${sp.wins}`} label="Wins" />
              <Stat value={`${sp.losses}`} label="Losses" />
              <Stat
                value={`${sp.matches_played > 0 ? Math.round((sp.wins / sp.matches_played) * 100) : 0}%`}
                label="Win Rate"
              />
            </div>
          )}

          <button
            onClick={() => followMut.mutate()}
            disabled={followMut.isPending}
            className={`w-full py-3 rounded-xl font-bold text-sm border transition-colors active:scale-[0.98] ${
              followingNow
                ? "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                : "bg-teal-glow/15 border-teal-glow/40 text-teal-glow hover:bg-teal-glow/25"
            }`}
          >
            {followingNow ? "Following ✓" : "Follow"}
          </button>
        </div>
      )}
    </OverlaySheet>
  );
}

function Stat({ value, label, accent }: { value: string; label: string; accent?: boolean }) {
  return (
    <div className="rounded-xl bg-navy-800 border border-white/5 p-3 text-center">
      <p className={`font-extrabold text-lg ${accent ? "text-teal-glow" : "text-white"}`}>{value}</p>
      <p className="text-white/45 text-[11px] mt-0.5">{label}</p>
    </div>
  );
}
