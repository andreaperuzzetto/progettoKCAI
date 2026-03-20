"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../lib/auth-context";
import { createRestaurant } from "../lib/api";
import { useState } from "react";

const links = [
  { href: "/", label: "Today" },
  { href: "/problems", label: "Problems" },
  { href: "/opportunities", label: "Opportunities" },
];

export default function Nav() {
  const pathname = usePathname();
  const { user, activeRestaurant, logout, selectRestaurant, refreshUser } = useAuth();
  const [creating, setCreating] = useState(false);

  async function handleCreateRestaurant() {
    const name = window.prompt("Restaurant name:");
    if (!name?.trim()) return;
    setCreating(true);
    try {
      await createRestaurant(name.trim());
      await refreshUser();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to create restaurant");
    } finally {
      setCreating(false);
    }
  }

  return (
    <nav className="flex items-center gap-4 border-b border-gray-200 px-6 py-4 flex-wrap">
      <span className="font-bold text-lg mr-6">Restaurant Intelligence</span>

      {user && links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`px-3 py-1 rounded transition-colors ${
            pathname === link.href
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          {link.label}
        </Link>
      ))}

      <div className="ml-auto flex items-center gap-3">
        {user && user.restaurants.length > 0 && (
          <select
            value={activeRestaurant?.id ?? ""}
            onChange={(e) => {
              const r = user.restaurants.find((r) => r.id === e.target.value);
              if (r) selectRestaurant(r);
            }}
            className="text-sm border rounded px-2 py-1 focus:outline-none"
          >
            {user.restaurants.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        )}

        {user && (
          <button
            onClick={handleCreateRestaurant}
            disabled={creating}
            title="Add restaurant"
            className="text-sm text-gray-500 hover:text-gray-900 border rounded px-2 py-1"
          >
            + Restaurant
          </button>
        )}

        {user ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 hidden sm:inline">{user.email}</span>
            <button
              onClick={logout}
              className="text-sm text-gray-600 hover:text-gray-900 border rounded px-2 py-1"
            >
              Sign out
            </button>
          </div>
        ) : (
          <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
            Sign in
          </Link>
        )}
      </div>
    </nav>
  );
}
