"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../lib/auth-context";
import { createRestaurant } from "../lib/api";
import { useState } from "react";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/billing", label: "Piano" },
];

export default function Nav() {
  const pathname = usePathname();
  const { user, activeRestaurant, logout, selectRestaurant, refreshUser } = useAuth();
  const [creating, setCreating] = useState(false);

  async function handleCreateRestaurant() {
    const name = window.prompt("Nome del ristorante:");
    if (!name?.trim()) return;
    setCreating(true);
    try {
      await createRestaurant(name.trim());
      await refreshUser();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Errore");
    } finally {
      setCreating(false);
    }
  }

  const isInactive = user?.subscription_status === "inactive";

  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-6 py-3 flex items-center gap-4 flex-wrap">
        {/* Brand */}
        <span className="font-bold text-gray-900 mr-2 shrink-0">🍽 Restaurant AI</span>

        {/* Nav links (only when logged in) */}
        {user && links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${
              pathname === link.href
                ? "bg-gray-900 text-white"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            {link.label}
          </Link>
        ))}

        {/* Subscription warning */}
        {user && isInactive && (
          <Link
            href="/billing"
            className="text-xs bg-amber-100 text-amber-800 px-2.5 py-1 rounded-full font-medium hover:bg-amber-200 transition-colors"
          >
            ⚠ Trial scaduto — Attiva il piano
          </Link>
        )}

        {/* Right side */}
        <div className="ml-auto flex items-center gap-2 flex-wrap">
          {/* Restaurant selector */}
          {user && user.restaurants.length > 1 && (
            <select
              value={activeRestaurant?.id ?? ""}
              onChange={(e) => {
                const r = user.restaurants.find((r) => r.id === e.target.value);
                if (r) selectRestaurant(r);
              }}
              className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
            >
              {user.restaurants.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          )}

          {/* Single restaurant name (no dropdown needed) */}
          {user && user.restaurants.length === 1 && activeRestaurant && (
            <span className="text-sm text-gray-500 hidden sm:inline">{activeRestaurant.name}</span>
          )}

          {user && (
            <button
              onClick={handleCreateRestaurant}
              disabled={creating}
              className="text-sm text-gray-500 hover:text-gray-900 border border-gray-200 rounded-lg px-2.5 py-1.5 hover:bg-gray-50 transition-colors disabled:opacity-50"
              title="Aggiungi ristorante"
            >
              + Ristorante
            </button>
          )}

          {user ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400 hidden md:inline">{user.email}</span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-900 border border-gray-200 rounded-lg px-2.5 py-1.5 hover:bg-gray-50 transition-colors"
              >
                Esci
              </button>
            </div>
          ) : (
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
              Accedi
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
