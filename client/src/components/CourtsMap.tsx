import { useEffect, useRef } from "react";

const DARK_TILES = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

export type MapCourt = { id: string | number; name: string; lat: number; lng: number; live?: boolean };

export function CourtsMap({
  height = "100%",
  interactive = true,
  courts = [],
  onCourtClick,
}: {
  height?: string | number;
  interactive?: boolean;
  courts?: MapCourt[];
  onCourtClick?: (id: string | number) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const clickRef = useRef(onCourtClick);
  clickRef.current = onCourtClick;

  useEffect(() => {
    if (typeof window === "undefined" || !ref.current) return;
    let map: any;
    let cancelled = false;

    (async () => {
      try {
        const mod: any = await import("leaflet");
        const L = mod.default ?? mod;
        if (cancelled || !ref.current) return;

        map = L.map(ref.current, {
          zoomControl: false,
          attributionControl: false,
          scrollWheelZoom: interactive,
          dragging: interactive,
          doubleClickZoom: interactive,
          touchZoom: interactive,
        }).setView([32.0853, 34.7818], 12);

        L.tileLayer(DARK_TILES, { attribution: TILE_ATTR, maxZoom: 19 }).addTo(map);

        // Auto-fit if we have courts
        if (courts.length > 0) {
          const bounds = L.latLngBounds(courts.map((c) => [c.lat, c.lng]));
          map.fitBounds(bounds, { padding: [24, 24], maxZoom: 13 });
        }

        courts.forEach((c) => {
          const icon = L.divIcon({
            className: "",
            html: `<div class="court-marker ${c.live ? "live" : "offline"}"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
          });
          const m = L.marker([c.lat, c.lng], { icon })
            .addTo(map)
            .bindTooltip(c.name, { className: "leaflet-tooltip-sportout", direction: "top", offset: [0, -8] });
          m.on("click", () => clickRef.current?.(c.id));
        });
      } catch (e) {
        console.error("Failed to load Leaflet", e);
      }
    })();

    return () => {
      cancelled = true;
      if (map) map.remove();
    };
  }, [interactive, courts]);

  return <div ref={ref} style={{ height, width: "100%" }} />;
}
