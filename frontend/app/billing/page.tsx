"use client";

import { useState } from "react";
import { useAuth } from "../lib/auth-context";
import { createCheckoutSession } from "../lib/api";

export default function BillingPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCheckout() {
    setLoading(true);
    setError("");
    try {
      const { checkout_url } = await createCheckoutSession();
      window.location.href = checkout_url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Errore durante il checkout");
    } finally {
      setLoading(false);
    }
  }

  const isActive = user?.subscription_status === "active";
  const isTrial = user?.subscription_status === "trial";

  return (
    <div className="max-w-lg mx-auto py-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Piano</h1>
      <p className="text-gray-500 mb-8">Gestisci il tuo abbonamento</p>

      {/* Current status */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-gray-700">Stato attuale</span>
          <StatusBadge status={user?.subscription_status ?? "inactive"} />
        </div>
        {isTrial && (
          <p className="text-sm text-blue-700 bg-blue-50 rounded-lg px-3 py-2">
            Sei in periodo di prova gratuito (7 giorni). Attiva il piano per continuare ad usare l'analisi AI dopo la scadenza.
          </p>
        )}
        {isActive && (
          <p className="text-sm text-green-700 bg-green-50 rounded-lg px-3 py-2">
            Il tuo abbonamento è attivo. Hai accesso completo a tutte le funzionalità.
          </p>
        )}
        {!isActive && !isTrial && (
          <p className="text-sm text-red-700 bg-red-50 rounded-lg px-3 py-2">
            Il tuo trial è scaduto. Attiva il piano per continuare.
          </p>
        )}
      </div>

      {/* Pricing card */}
      {!isActive && (
        <div className="bg-gray-900 text-white rounded-xl p-6">
          <div className="flex items-baseline gap-1 mb-1">
            <span className="text-4xl font-bold">€29</span>
            <span className="text-gray-400">/mese</span>
          </div>
          <p className="text-gray-400 text-sm mb-6">Accesso completo alla piattaforma</p>

          <ul className="space-y-2 mb-8 text-sm">
            {[
              "Analisi AI illimitata delle recensioni",
              "Problemi, punti di forza e suggerimenti operativi",
              "Upload CSV e testo libero",
              "Multi-ristorante",
              "Dashboard aggiornabile in tempo reale",
            ].map((feat) => (
              <li key={feat} className="flex items-center gap-2 text-gray-300">
                <span className="text-green-400">✓</span> {feat}
              </li>
            ))}
          </ul>

          {error && (
            <p className="text-red-400 text-sm mb-3">{error}</p>
          )}

          <button
            onClick={handleCheckout}
            disabled={loading}
            className="w-full bg-white text-gray-900 font-semibold py-3 rounded-lg hover:bg-gray-100 disabled:opacity-50 transition-colors"
          >
            {loading ? "Reindirizzamento..." : "Attiva ora →"}
          </button>
          <p className="text-xs text-gray-500 text-center mt-3">Pagamento sicuro via Stripe · Cancellazione in qualsiasi momento</p>
        </div>
      )}

      {isActive && (
        <p className="text-sm text-gray-500 text-center">
          Per gestire o cancellare l'abbonamento, contatta il supporto.
        </p>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    active: { label: "Attivo", cls: "bg-green-100 text-green-800" },
    trial: { label: "Trial gratuito", cls: "bg-blue-100 text-blue-800" },
    inactive: { label: "Scaduto", cls: "bg-red-100 text-red-800" },
  };
  const c = map[status] ?? map.inactive;
  return <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${c.cls}`}>{c.label}</span>;
}
