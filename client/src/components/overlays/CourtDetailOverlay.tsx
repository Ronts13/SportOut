import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCourtDetail } from "@/lib/api";
import { OverlaySheet } from "./Sheet";
import { CreateMatchOverlay } from "./CreateMatchOverlay";
import { Lightbulb, Clock, MapPin } from "lucide-react";

export function CourtDetailOverlay({ courtId, onClose }: { courtId: string | null; onClose: () => void }) {
  const open = !!courtId;
  const [createOpen, setCreateOpen] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["court-detail", courtId],
    queryFn: () => fetchCourtDetail(courtId!),
    enabled: open,
  });

  return (
    <>
      <OverlaySheet open={open} onClose={onClose} title={data?.facility?.name ?? data?.name ?? "Court"}>
        {isLoading || !data ? (
          <div className="p-6 text-white/50 text-sm">Loading…</div>
        ) : (
          <div className="p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-bold text-lg">{data.facility?.name ?? data.name}</p>
                <p className="text-white/40 text-xs flex items-center gap-1 mt-0.5">
                  <MapPin className="w-3 h-3" />
                  {data.facility?.address_city ?? "—"} · {data.sport}
                </p>
              </div>
              {data.current_occupancy > 0 && (
                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-teal-glow/15 border border-teal-glow/40">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-glow live-dot" />
                  <span className="text-teal-glow text-[10px] font-bold uppercase tracking-widest">Live</span>
                </span>
              )}
            </div>

            <div className="grid grid-cols-3 gap-2">
              <Stat value={`${data.current_occupancy}`} label="On court" accent />
              <Stat value={`${data.max_capacity}`} label="Capacity" />
              <Stat value={data.indoor ? "Indoor" : "Outdoor"} label="Type" />
            </div>

            <div className="flex flex-col gap-2">
              <Row icon={<Clock className="w-4 h-4 text-teal-glow/70" />} label="Hours">
                {data.facility?.opens_at && data.facility?.closes_at
                  ? `${data.facility.opens_at.slice(0, 5)} – ${data.facility.closes_at.slice(0, 5)}`
                  : "—"}
              </Row>
              <Row icon={<Lightbulb className="w-4 h-4 text-teal-glow/70" />} label="Lighting">
                {data.lighting_available ? (data.lighting_on ? "On now" : "Available") : "Not available"}
              </Row>
              <Row icon={<MapPin className="w-4 h-4 text-teal-glow/70" />} label="Surface">
                {data.surface}
              </Row>
            </div>

            <button
              onClick={() => setCreateOpen(true)}
              className="w-full py-3 rounded-xl bg-teal-glow/15 border border-teal-glow/40 text-teal-glow font-bold text-sm hover:bg-teal-glow/25 active:scale-[0.98] transition-colors"
            >
              Create match here
            </button>
          </div>
        )}
      </OverlaySheet>
      <CreateMatchOverlay open={createOpen} onClose={() => setCreateOpen(false)} />
    </>
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

function Row({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-navy-800 border border-white/5">
      {icon}
      <span className="text-white/45 text-xs flex-1">{label}</span>
      <span className="text-white text-sm font-semibold">{children}</span>
    </div>
  );
}
