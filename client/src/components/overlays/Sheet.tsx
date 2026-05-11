import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

export function OverlaySheet({
  open,
  onClose,
  title,
  children,
  fullscreen = false,
}: {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  fullscreen?: boolean;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[180] bg-black/70 backdrop-blur-sm flex items-end lg:items-center justify-center" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className={
          fullscreen
            ? "w-full h-[100dvh] bg-navy-950 flex flex-col overflow-hidden"
            : "w-full lg:max-w-md max-h-[92dvh] bg-navy-900 border border-white/10 rounded-t-3xl lg:rounded-3xl flex flex-col overflow-hidden"
        }
      >
        <div className="sticky top-0 z-10 flex items-center gap-3 px-4 safe-pt pb-3 bg-navy-950/95 border-b border-white/5 backdrop-blur-md">
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-navy-800 border border-white/10 flex items-center justify-center hover:border-teal-glow/40 active:scale-95"
          >
            <X className="w-4 h-4 text-white/70" />
          </button>
          <span className="text-white font-bold text-base flex-1 truncate">{title}</span>
        </div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
