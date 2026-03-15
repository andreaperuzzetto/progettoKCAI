"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Today" },
  { href: "/problems", label: "Problems" },
  { href: "/opportunities", label: "Opportunities" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-4 border-b border-gray-200 px-6 py-4">
      <span className="font-bold text-lg mr-6">Restaurant Intelligence</span>
      {links.map((link) => (
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
    </nav>
  );
}
