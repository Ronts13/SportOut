import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/use-auth";
import { fetchPlayerDetail, getMyPlayer, getMyProfile, updateMyProfile } from "@/lib/api";
import { useNavigate } from "@tanstack/react-router";
import { LogOut, Save } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/profile")({
  head: () => ({
    meta: [
      { title: "Profile — SportOut" },
      { name: "description", content: "Your SportOut profile, stats and highlights." },
    ],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const qc = useQueryClient();
  const { session, signOut } = useAuth();
  const navigate = useNavigate();
  const { data: profile } = useQuery({ queryKey: ["my-profile", session?.user.id], queryFn: getMyProfile, enabled: !!session });
  const { data: player } = useQuery({ queryKey: ["my-player"], queryFn: getMyPlayer, enabled: !!session });
  const { data: detail } = useQuery({
    queryKey: ["player-detail", player?.id],
    queryFn: () => fetchPlayerDetail(player!.id),
    enabled: !!player?.id,
  });

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ display_name: "", handle: "", city: "", bio: "" });
  useEffect(() => {
    if (profile) setForm({
      display_name: profile.display_name ?? "",
      handle: profile.handle ?? "",
      city: profile.city ?? "",
      bio: profile.bio ?? "",
    });
  }, [profile]);

  const save = useMutation({
    mutationFn: () => updateMyProfile(form),
    onSuccess: () => {
      toast.success("Profile updated");
      qc.invalidateQueries({ queryKey: ["my-profile"] });
      qc.invalidateQueries({ queryKey: ["my-player"] });
      setEditing(false);
    },
    onError: (e: any) => toast.error(e?.message ?? "Failed"),
  });

  const [activeSport, setActiveSport] = useState<string | null>(null);
  useEffect(() => {
    if (detail?.sports.length && !activeSport) setActiveSport(detail.sports[0].sport);
  }, [detail, activeSport]);
  const sp = detail?.sports.find((s: any) => s.sport === activeSport) ?? detail?.sports[0];

  const initial = (profile?.display_name ?? session?.user.email ?? "?").charAt(0).toUpperCase();

  return (
    <AppShell title="Profile">
      <div className="px-4 lg:px-8 pt-4 pb-6 flex flex-col items-center bg-gradient-to-b from-navy-800/50 to-transparent">
        <div className="w-20 h-20 rounded-full bg-navy-700 border-2 border-teal-glow/50 shadow-teal-glow flex items-center justify-center mb-3">
          <span className="text-teal-glow text-3xl font-extrabold">{initial}</span>
        </div>
        <p className="text-white font-bold text-lg tracking-tight">{profile?.display_name ?? "Player"}</p>
        {profile?.handle && <p className="text-teal-glow/80 text-xs mt-0.5">@{profile.handle}</p>}
        <p className="text-white/40 text-sm mt-0.5">{profile?.city ?? player?.home_city ?? "—"}</p>
        {profile?.bio && <p className="text-white/50 text-xs mt-2 max-w-xs text-center">{profile.bio}</p>}

        <div className="flex items-center justify-around w-full mt-4 px-4 max-w-sm">
          <Stat value={`${Math.round(sp?.rating ?? 1200)}`} label="Rating" accent />
          <Sep />
          <Stat value={`${detail?.followers ?? 0}`} label="Followers" />
          <Sep />
          <Stat value={`${detail?.following ?? 0}`} label="Following" />
        </div>

        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setEditing((v) => !v)}
            className="px-6 py-2 rounded-xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow text-sm font-semibold hover:bg-teal-glow/20"
          >
            {editing ? "Cancel" : "Edit Profile"}
          </button>
          <button
            onClick={() => { signOut(); navigate({ to: "/auth" }); }}
            className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white/70 text-sm font-semibold hover:bg-white/10 inline-flex items-center gap-1.5"
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      </div>

      {editing && (
        <div className="mx-4 lg:mx-8 mb-5 p-4 rounded-2xl bg-navy-800 border border-white/10 flex flex-col gap-3">
          <Field label="Display name">
            <input className="cm-input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
          </Field>
          <Field label="Handle">
            <input className="cm-input" value={form.handle} onChange={(e) => setForm({ ...form, handle: e.target.value })} />
          </Field>
          <Field label="City">
            <input className="cm-input" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          </Field>
          <Field label="Bio">
            <textarea rows={3} className="cm-input resize-none" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
          </Field>
          <button
            onClick={() => save.mutate()}
            disabled={save.isPending}
            className="w-full py-2.5 rounded-xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow text-sm font-bold hover:bg-teal-glow/25 inline-flex items-center justify-center gap-1.5"
          >
            <Save className="w-4 h-4" /> {save.isPending ? "Saving…" : "Save"}
          </button>
          <style>{`.cm-input{width:100%;background:var(--navy-900);border:1px solid rgba(255,255,255,.1);border-radius:.75rem;padding:.6rem .9rem;font-size:.875rem;color:rgba(255,255,255,.9);outline:none}.cm-input:focus{border-color:rgba(0,255,231,.4)}`}</style>
        </div>
      )}

      {detail && detail.sports.length > 0 && (
        <>
          <div className="flex gap-2 overflow-x-auto no-scrollbar px-4 lg:px-8 mb-3">
            {detail.sports.map((s: any) => (
              <button key={s.sport} onClick={() => setActiveSport(s.sport)} className={`sport-chip ${activeSport === s.sport ? "active" : ""}`}>
                {s.sport}
              </button>
            ))}
          </div>

          {sp && (
            <div className="px-4 lg:px-8 mb-5 grid grid-cols-3 gap-3">
              <MiniStat value={`${sp.wins}`} label="Wins" />
              <MiniStat value={`${sp.losses}`} label="Losses" />
              <MiniStat value={`${sp.matches_played > 0 ? Math.round((sp.wins / sp.matches_played) * 100) : 0}%`} label="Win Rate" />
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}

function Stat({ value, label, accent }: { value: string; label: string; accent?: boolean }) {
  return (
    <div className="text-center">
      <p className={`font-extrabold text-xl leading-tight ${accent ? "text-teal-glow" : "text-white"}`}>{value}</p>
      <p className="text-white/40 text-[11px] mt-0.5">{label}</p>
    </div>
  );
}
function Sep() { return <div className="w-px h-8 bg-white/10" />; }
function MiniStat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-2xl bg-navy-800 border border-white/5 p-4 text-center shadow-card">
      <p className="text-teal-glow text-xl font-extrabold">{value}</p>
      <p className="text-white/50 text-[11px] mt-1 font-medium">{label}</p>
    </div>
  );
}
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs uppercase tracking-wide text-white/40 font-semibold">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
