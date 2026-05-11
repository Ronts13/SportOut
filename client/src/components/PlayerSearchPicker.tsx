import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchPlayers } from "@/lib/api";
import { Search, Check, X } from "lucide-react";
import { SPORTS } from "@/data/mock";

const CITIES = ["All Cities", "Tel Aviv", "Herzliya", "Ramat Gan", "Jerusalem", "Haifa", "Holon", "Petah Tikva", "Givatayim"];

export type PickedPlayer = { id: string; user_id: string; display_name: string; home_city: string | null };

export function PlayerSearchPicker({
  value,
  onChange,
  sport,
  max = 20,
}: {
  value: PickedPlayer[];
  onChange: (next: PickedPlayer[]) => void;
  sport?: string;
  max?: number;
}) {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [filterSport, setFilterSport] = useState<string>(sport ?? "All Sports");
  const [filterCity, setFilterCity] = useState<string>("All Cities");
  const [followingOnly, setFollowingOnly] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q.trim()), 200);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    if (sport) setFilterSport(sport);
  }, [sport]);

  const { data: results = [], isFetching } = useQuery({
    queryKey: ["search-players", debouncedQ, filterSport, filterCity, followingOnly],
    queryFn: () =>
      searchPlayers({
        q: debouncedQ || undefined,
        sport: filterSport === "All Sports" ? null : filterSport,
        city: filterCity === "All Cities" ? null : filterCity,
        followingOnly,
      }),
  });

  const selectedIds = useMemo(() => new Set(value.map((v) => v.id)), [value]);

  const toggle = (p: PickedPlayer) => {
    if (selectedIds.has(p.id)) onChange(value.filter((v) => v.id !== p.id));
    else if (value.length < max) onChange([...value, p]);
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search players by name…"
          className="w-full bg-navy-800 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white/90 placeholder-white/25 outline-none focus:border-teal-glow/40"
        />
      </div>

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto no-scrollbar">
        {SPORTS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setFilterSport(s)}
            className={`sport-chip ${filterSport === s ? "active" : ""}`}
          >
            {s}
          </button>
        ))}
      </div>
      <div className="flex gap-2 overflow-x-auto no-scrollbar">
        {CITIES.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setFilterCity(c)}
            className={`sport-chip ${filterCity === c ? "active" : ""}`}
          >
            {c}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setFollowingOnly((v) => !v)}
          className={`sport-chip ${followingOnly ? "active" : ""}`}
        >
          👥 Following
        </button>
      </div>

      {/* Selected chips */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((p) => (
            <span
              key={p.id}
              className="inline-flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-full bg-teal-glow/15 border border-teal-glow/40 text-teal-glow text-xs font-semibold"
            >
              {p.display_name}
              <button
                type="button"
                onClick={() => toggle(p)}
                className="w-4 h-4 rounded-full bg-teal-glow/20 flex items-center justify-center hover:bg-teal-glow/30"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Results */}
      <div className="max-h-72 overflow-y-auto rounded-xl border border-white/5 divide-y divide-white/5">
        {isFetching && <p className="p-3 text-white/40 text-xs">Searching…</p>}
        {!isFetching && results.length === 0 && <p className="p-3 text-white/40 text-xs">No players match.</p>}
        {results.map((p: any) => {
          const picked = selectedIds.has(p.id);
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => toggle(p)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors ${
                picked ? "bg-teal-glow/10" : "bg-navy-800 hover:bg-navy-700"
              }`}
            >
              <div className="w-8 h-8 rounded-full bg-navy-700 border border-teal-glow/30 flex items-center justify-center text-teal-glow font-bold text-xs flex-shrink-0">
                {(p.display_name || "?").charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-semibold truncate">{p.display_name}</p>
                <p className="text-white/40 text-xs truncate">
                  {p.home_city ?? "—"} · {(p.preferred_sports ?? []).slice(0, 2).join(", ") || "Player"}
                </p>
              </div>
              <div
                className={`w-6 h-6 rounded-full border flex items-center justify-center flex-shrink-0 ${
                  picked ? "bg-teal-glow border-teal-glow" : "border-white/15"
                }`}
              >
                {picked && <Check className="w-3.5 h-3.5 text-navy-950" />}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
