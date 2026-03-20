"use client";

import { useState } from "react";
import { createCheckoutSession } from "../lib/api";
import { useAuth } from "../lib/auth-context";
import Link from "next/link";

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    price: "49",
    label: "Per iniziare",
    color: "border-gray-200",
    badge: "",
    features: [
      { text: "Import recensioni (CSV + testo)", included: true },
      { text: "Analisi LLM: sentiment + problemi", included: true },
      { text: "Suggerimenti operativi base", included: true },
      { text: "Dashboard unificata", included: true },
      { text: "Previsioni domanda", included: false },
      { text: "Alert automatici", included: false },
      { text: "Analisi causale avanzata", included: false },
      { text: "Integrazioni POS automatiche", included: false },
    ],
  },
  {
    id: "pro",
    name: "Pro",
    price: "99",
    label: "Consigliato per la maggior parte",
    color: "border-gray-900 ring-2 ring-gray-900",
    badge: "Consigliato",
    features: [
      { text: "Import recensioni (CSV + testo)", included: true },
      { text: "Analisi LLM: sentiment + problemi", included: true },
      { text: "Suggerimenti operativi base", included: true },
      { text: "Dashboard unificata", included: true },
      { text: "Previsioni domanda (7 giorni)", included: true },
      { text: "Alert automatici (alta domanda, calo vendite…)", included: true },
      { text: "Analisi causale avanzata", included: false },
      { text: "Integrazioni POS automatiche", included: false },
    ],
  },
  {
    id: "premium",
    name: "Premium",
    price: "199",
    label: "Per chi vuole il massimo",
    color: "border-purple-300",
    badge: "",
    features: [
      { text: "Import recensioni (CSV + testo)", included: true },
      { text: "Analisi LLM: sentiment + problemi", included: true },
      { text: "Suggerimenti operativi base", included: true },
      { text: "Dashboard unificata", included: true },
      { text: "Previsioni domanda (7 giorni)", included: true },
      { text: "Alert automatici (alta domanda, calo vendite…)", included: true },
      { text: "Analisi causale avanzata (LLM)", included: true },
      { text: "Integrazioni POS automatiche (Square, Toast…)", included: true },
    ],
  },
] as const;

export default function BillingPage() {
  const { user } = useAuth();
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleCheckout(planId: "starter" | "pro" | "premium") {
    setError("");
    setLoadingPlan(planId);
    try {
      const res = await createCheckoutSession(planId);
      if (res.checkout_url) window.location.href = res.checkout_url;
      else setError("URL checkout non disponibile — configura STRIPE_PRICE_ID nel backend.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Errore checkout");
    } finally {
      setLoadingPlan(null);
    }
  }

  const currentPlan = user?.plan ?? "starter";
  const isActive = user?.subscription_status === "active";
  const isTrial = user?.subscription_status === "trial";

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Scegli il tuo piano</h1>
        <p className="text-gray-500 text-sm">
          Inizia con 7 giorni di prova gratuita · Annulla quando vuoi
        </p>
        {isTrial && (
          <div className="mt-3 inline-flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-2 rounded-full">
            ⏳ Prova in corso — scegli un piano per continuare dopo la scadenza
          </div>
        )}
        {isActive && (
          <div className="mt-3 inline-flex items-center gap-2 bg-green-50 border border-green-200 text-green-800 text-sm px-4 py-2 rounded-full">
            ✅ Piano attivo: <strong className="capitalize">{currentPlan}</strong>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl mb-6 text-center">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map(plan => {
          const isCurrent = currentPlan === plan.id && isActive;
          return (
            <div key={plan.id} className={`relative bg-white rounded-2xl border p-6 flex flex-col ${plan.color}`}>
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gray-900 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    {plan.badge}
                  </span>
                </div>
              )}

              <div className="mb-4">
                <h2 className="text-lg font-bold text-gray-900">{plan.name}</h2>
                <p className="text-xs text-gray-400 mt-0.5">{plan.label}</p>
                <div className="mt-3">
                  <span className="text-4xl font-bold text-gray-900">{plan.price}€</span>
                  <span className="text-sm text-gray-500 ml-1">/mese</span>
                </div>
              </div>

              <ul className="space-y-2.5 flex-1 mb-6">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm">
                    <span className={f.included ? "text-green-500 shrink-0 mt-0.5" : "text-gray-300 shrink-0 mt-0.5"}>
                      {f.included ? "✓" : "✕"}
                    </span>
                    <span className={f.included ? "text-gray-700" : "text-gray-400 line-through"}>
                      {f.text}
                    </span>
                  </li>
                ))}
              </ul>

              {isCurrent ? (
                <div className="text-center py-2.5 bg-green-50 text-green-700 text-sm font-medium rounded-xl border border-green-200">
                  Piano attuale
                </div>
              ) : (
                <button
                  onClick={() => handleCheckout(plan.id as "starter" | "pro" | "premium")}
                  disabled={!!loadingPlan}
                  className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 ${
                    plan.id === "pro"
                      ? "bg-gray-900 text-white hover:bg-gray-700"
                      : "border border-gray-300 text-gray-800 hover:bg-gray-50"
                  }`}
                >
                  {loadingPlan === plan.id ? "Caricamento…" : `Inizia con ${plan.name}`}
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className="text-center mt-8">
        <p className="text-xs text-gray-400">
          Pagamento sicuro via Stripe · IVA non inclusa · Rinnovo mensile automatico
        </p>
        {user && (
          <Link href="/" className="block mt-3 text-xs text-gray-400 underline hover:text-gray-600">
            ← Torna alla dashboard
          </Link>
        )}
      </div>
    </div>
  );
}
