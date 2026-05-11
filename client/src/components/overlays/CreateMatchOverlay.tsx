import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createMatch, fetchCourts } from "@/lib/api";
import { OverlaySheet } from "./Sheet";
import { PlayerSearchPicker, type PickedPlayer } from "@/components/PlayerSearchPicker";
import { toast } from "sonner";

const SPORT_OPTS = [
  { id: "Padel", emoji: "🎾" },
  { id: "Tennis", emoji: "🎾" },
  { id: "Football", emoji: "⚽" },
  { id: "Basketball", emoji: "🏀" },
  { id: "Table Tennis", emoji: "🏓" },
  { id: "Footvolley", emoji: "🏐" },
  { id: "Boxing", emoji: "🥊" },
];
const FORMATS = ["1v1", "2v2", "3v3", "4v4", "5v5"];

const formatToMaxPlayers = (f: string) => {
  const m = f.match(/(\d+)v(\d+)/);
  return m ? parseInt(m[1]) + parseInt(m[2]) : 4;
};

export function CreateMatchOverlay({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const { data: courts = [] } = useQuery({ queryKey: ["courts"], queryFn: fetchCourts });

  const [sport, setSport] = useState("Tennis");
  const [courtId, setCourtId] = useState<string>("");
  const [format, setFormat] = useState("2v2");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [time, setTime] = useState(() => {
    const d = new Date(Date.now() + 60 * 60 * 1000);
    d.setMinutes(0, 0, 0);
    return d.toTimeString().slice(0, 5);
  });
  const [minRating, setMinRating] = useState<number>(0);
  const [maxRating, setMaxRating] = useState<number>(0);
  const [isPrivate, setIsPrivate] = useState(false);
  const [invited, setInvited] = useState<PickedPlayer[]>([]);

  const sportCourts = useMemo(
    () => courts.filter((c) => c.sport.toLowerCase() === sport.toLowerCase()),
    [courts, sport]
  );

  const submit = useMutation({
    mutationFn: () => {
      const scheduled = new Date(`${date}T${time}:00`);
      const max = formatToMaxPlayers(format);
      const court = courts.find((c) => c.id === courtId);
      return createMatch({
        sport,
        format,
        max_players: max,
        scheduled_at: scheduled.toISOString(),
        court_id: courtId || null,
        facility_id: court?.facility?.id ?? null,
        min_rating: minRating > 0 ? minRating : null,
        max_rating: maxRating > 0 ? maxRating : null,
        is_private: isPrivate,
        invite_player_ids: invited.map((i) => i.id),
      });
    },
    onSuccess: () => {
      toast.success("Match published 🎉");
      qc.invalidateQueries({ queryKey: ["matches"] });
      onClose();
      setInvited([]);
    },
    onError: (e: any) => toast.error(e?.message ?? "Could not create match"),
  });

  return (
    <OverlaySheet open={open} onClose={onClose} fullscreen title="Create a Match">
      <div className="px-4 pt-6 pb-12 flex flex-col gap-6 max-w-2xl mx-auto w-full">
        <Section label="Sport">
          <div className="grid grid-cols-3 gap-2">
            {SPORT_OPTS.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => {
                  setSport(s.id);
                  setCourtId("");
                }}
                className={`px-3 py-2.5 rounded-xl text-xs font-semibold border transition-colors ${
                  sport === s.id
                    ? "bg-teal-glow/15 border-teal-glow/40 text-teal-glow"
                    : "bg-navy-800 border-white/10 text-white/60 hover:border-white/20"
                }`}
              >
                <span className="mr-1">{s.emoji}</span>
                {s.id}
              </button>
            ))}
          </div>
        </Section>

        <Section label={`Venue (${sportCourts.length})`}>
          <VenuePicker
            courts={sportCourts}
            value={courtId}
            onChange={setCourtId}
          />
        </Section>

        <Section label="Date & Time">
          <div className="flex gap-2">
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="cm-input" />
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className="cm-input" />
          </div>
        </Section>

        <Section label="Format">
          <div className="flex gap-2 flex-wrap">
            {FORMATS.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFormat(f)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold border transition-colors ${
                  format === f
                    ? "bg-teal-glow/15 border-teal-glow/40 text-teal-glow"
                    : "bg-navy-800 border-white/10 text-white/60"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <p className="text-white/40 text-xs mt-2">
            Total slots: <span className="text-white font-semibold">{formatToMaxPlayers(format)}</span>
          </p>
        </Section>

        <Section label="Skill range (optional)">
          <div className="flex gap-2 items-center">
            <select value={minRating} onChange={(e) => setMinRating(parseInt(e.target.value))} className="cm-input">
              <option value="0">Min: any</option>
              {[800, 1000, 1200, 1400, 1600, 1800, 2000].map((v) => (
                <option key={v} value={v}>{`Min ${v}`}</option>
              ))}
            </select>
            <select value={maxRating} onChange={(e) => setMaxRating(parseInt(e.target.value))} className="cm-input">
              <option value="0">Max: any</option>
              {[1200, 1400, 1600, 1800, 2000, 2400].map((v) => (
                <option key={v} value={v}>{`Max ${v}`}</option>
              ))}
            </select>
          </div>
        </Section>

        <Section label="Privacy">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setIsPrivate(false)}
              className={`flex-1 px-3 py-2.5 rounded-xl text-xs font-semibold border transition-colors ${
                !isPrivate ? "bg-teal-glow/15 border-teal-glow/40 text-teal-glow" : "bg-navy-800 border-white/10 text-white/60"
              }`}
            >
              🌍 Public lobby
            </button>
            <button
              type="button"
              onClick={() => setIsPrivate(true)}
              className={`flex-1 px-3 py-2.5 rounded-xl text-xs font-semibold border transition-colors ${
                isPrivate ? "bg-teal-glow/15 border-teal-glow/40 text-teal-glow" : "bg-navy-800 border-white/10 text-white/60"
              }`}
            >
              🔒 Invite only
            </button>
          </div>
        </Section>

        <Section label={`Invite players (${invited.length})`}>
          <PlayerSearchPicker value={invited} onChange={setInvited} sport={sport} max={formatToMaxPlayers(format) - 1} />
        </Section>

        <button
          onClick={() => submit.mutate()}
          disabled={submit.isPending || !courtId}
          className="w-full py-4 rounded-2xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow font-bold text-base hover:bg-teal-glow/20 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-2"
        >
          {submit.isPending ? "Publishing…" : "Publish Match"}
        </button>
      </div>

      <style>{`.cm-input{width:100%;background:var(--navy-800);border:1px solid rgba(255,255,255,.1);border-radius:.75rem;padding:.65rem .9rem;font-size:.875rem;color:rgba(255,255,255,.9);outline:none}.cm-input:focus{border-color:rgba(0,255,231,.4)}`}</style>
    </OverlaySheet>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-white/35 text-[10px] font-semibold uppercase tracking-widest mb-3">{label}</p>
      {children}
    </div>
  );
}

function VenuePicker({
  courts,
  value,
  onChange,
}: {
  courts: any[];
  value: string;
  onChange: (id: string) => void;
}) {
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    const list = term
      ? courts.filter((c) => {
          const n = (c.facility?.name ?? c.name ?? "").toLowerCase();
          const city = (c.facility?.address_city ?? "").toLowerCase();
          return n.includes(term) || city.includes(term);
        })
      : courts;
    const groups: Record<string, any[]> = {};
    for (const c of list) {
      const city = c.facility?.address_city || "Other";
      (groups[city] ||= []).push(c);
    }
    return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]));
  }, [courts, q]);

  const selected = courts.find((c) => c.id === value);

  return (
    <div className="flex flex-col gap-2">
      {selected && (
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-teal-glow/10 border border-teal-glow/40">
          <span className="text-teal-glow text-sm font-semibold flex-1 truncate">
            ✓ {selected.facility?.name ?? selected.name}
          </span>
          <button
            type="button"
            onClick={() => onChange("")}
            className="text-teal-glow/60 text-xs hover:text-teal-glow"
          >
            Change
          </button>
        </div>
      )}
      {!selected && (
        <>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={`Search ${courts.length} courts by name or city…`}
            className="cm-input"
          />
          <div className="max-h-72 overflow-y-auto rounded-xl bg-navy-800 border border-white/10 divide-y divide-white/5">
            {filtered.length === 0 && (
              <p className="p-4 text-white/40 text-xs text-center">No matches</p>
            )}
            {filtered.map(([city, list]) => (
              <div key={city}>
                <p className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-widest text-white/35 sticky top-0 bg-navy-800/95 backdrop-blur">
                  {city} · {list.length}
                </p>
                {list.slice(0, 50).map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => onChange(c.id)}
                    className="w-full text-left px-3 py-2.5 hover:bg-teal-glow/10 transition-colors"
                  >
                    <p className="text-white text-sm font-medium truncate">
                      {c.facility?.name ?? c.name}
                    </p>
                    <p className="text-white/40 text-[11px] truncate">
                      {c.indoor ? "Indoor" : "Outdoor"} · {c.surface}
                      {c.lighting_available ? " · Lit" : ""}
                    </p>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
