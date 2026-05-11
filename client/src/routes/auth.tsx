import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { apiPost } from "@/lib/fastapi";
import { setToken } from "@/lib/fastapi";
import { toast } from "sonner";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
});

function AuthPage() {
  const navigate = useNavigate();
  const { session, signIn } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (session) navigate({ to: "/" });
  }, [session, navigate]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === "signup") {
        await apiPost("/players/", {
          email,
          password,
          display_name: displayName || email.split("@")[0],
          username: username || email.split("@")[0].replace(/[^a-zA-Z0-9_]/g, "_"),
        });
        toast.success("Account created! Signing you in…");
      }
      await signIn(email, password);
      navigate({ to: "/" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-navy-950 text-foreground flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-10 h-10 rounded-2xl bg-teal-base/20 border border-teal-glow/40 flex items-center justify-center">
            <span className="text-teal-glow font-extrabold text-lg">S</span>
          </div>
          <span className="text-foreground font-bold text-2xl tracking-tight">SportOut</span>
        </div>

        <div className="bg-navy-900/60 border border-white/10 rounded-3xl p-6 backdrop-blur-md">
          <h1 className="text-xl font-bold mb-1">{mode === "signin" ? "Welcome back" : "Create your account"}</h1>
          <p className="text-sm text-white/50 mb-6">
            {mode === "signin" ? "Find courts, matches, and players near you." : "Join the local sports community."}
          </p>

          <form onSubmit={submit} className="space-y-3">
            {mode === "signup" && (
              <>
                <input
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Display name (e.g. Ron Cohen)"
                  className="w-full rounded-xl bg-navy-800 border border-white/10 px-4 py-2.5 text-sm placeholder:text-white/30 focus:border-teal-glow/50 outline-none"
                />
                <input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Username (letters, numbers, _)"
                  className="w-full rounded-xl bg-navy-800 border border-white/10 px-4 py-2.5 text-sm placeholder:text-white/30 focus:border-teal-glow/50 outline-none"
                />
              </>
            )}
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-xl bg-navy-800 border border-white/10 px-4 py-2.5 text-sm placeholder:text-white/30 focus:border-teal-glow/50 outline-none"
            />
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password (min 8 chars)"
              className="w-full rounded-xl bg-navy-800 border border-white/10 px-4 py-2.5 text-sm placeholder:text-white/30 focus:border-teal-glow/50 outline-none"
            />
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-xl bg-teal-glow text-navy-950 font-semibold py-2.5 hover:bg-teal-glow/90 transition disabled:opacity-60"
            >
              {busy ? "…" : mode === "signin" ? "Sign in" : "Create account"}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-white/50">
            {mode === "signin" ? "New here?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
              className="text-teal-glow font-semibold hover:underline"
            >
              {mode === "signin" ? "Create an account" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
