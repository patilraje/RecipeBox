"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
  const router = useRouter();
  const { configured, signIn, signUp, user, loading } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/");
    }
  }, [loading, user, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setBusy(true);
    try {
      if (mode === "signin") {
        await signIn(email.trim(), password);
        router.push("/");
      } else {
        const message = await signUp(email.trim(), password);
        if (message) {
          setInfo(message);
          setMode("signin");
        } else {
          router.push("/");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  if (!configured) {
    return (
      <main className="page">
        <section className="panel auth-panel">
          <h2>Login unavailable</h2>
          <p className="muted">
            Add your free Supabase project keys to <code>.env.local</code>:
          </p>
          <pre className="code-block">{`NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...`}</pre>
          <p className="muted">
            Then run the SQL in <code>supabase/schema.sql</code> and restart the
            frontend.
          </p>
          <Link href="/" className="primary-button" style={{ display: "inline-block", marginTop: "1rem" }}>
            Back home
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <section className="panel auth-panel">
        <div className="section-intro">
          <h2>{mode === "signin" ? "Sign in" : "Create account"}</h2>
          <p>
            Save your pantry and favourites to your RecipeBox account (Supabase free
            tier).
          </p>
        </div>

        <form className="auth-form" onSubmit={onSubmit}>
          <label className="field-label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="text-input"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <label className="field-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="text-input"
            type="password"
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <div className="actions-row">
            <button type="submit" className="primary-button" disabled={busy}>
              {busy ? "Please wait…" : mode === "signin" ? "Sign in" : "Sign up"}
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => {
                setMode(mode === "signin" ? "signup" : "signin");
                setError(null);
                setInfo(null);
              }}
            >
              {mode === "signin" ? "Need an account?" : "Have an account?"}
            </button>
          </div>
        </form>

        {error && <div className="error-banner">{error}</div>}
        {info && <div className="info-banner">{info}</div>}
      </section>
    </main>
  );
}
