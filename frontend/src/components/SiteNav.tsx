"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const links = [
  { href: "/", label: "Find" },
  { href: "/pantry", label: "Pantry" },
  { href: "/results", label: "Results" },
  { href: "/favourites", label: "Saved" },
];

export function SiteNav() {
  const pathname = usePathname();
  const { configured, user, loading, signOut } = useAuth();

  return (
    <header className="site-nav">
      <Link href="/" className="brand-mark">
        RecipeBox
      </Link>
      <nav className="nav-links" aria-label="Primary">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={pathname === link.href ? "nav-link active" : "nav-link"}
          >
            {link.label}
          </Link>
        ))}
        {configured && !loading && user ? (
          <>
            <span className="nav-user" title={user.email || ""}>
              {user.email?.split("@")[0]}
            </span>
            <button type="button" className="nav-link nav-button" onClick={() => signOut()}>
              Sign out
            </button>
          </>
        ) : (
          <Link
            href="/login"
            className={pathname === "/login" ? "nav-link active" : "nav-link"}
          >
            Sign in
          </Link>
        )}
      </nav>
    </header>
  );
}
