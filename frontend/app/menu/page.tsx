"use client";

import { useState } from "react";
import { useAuth } from "../lib/auth-context";
import {
  analyzeMenu,
  fetchMenuMetrics,
  uploadSalesCsv,
  MenuSuggestion,
  ProductMetric,
} from "../lib/api";

const ACTION_LABELS: Record<MenuSuggestion["action"], { label: string; color: string; icon: string }> = {
  promote:        { label: "Promuovi",        color: "bg-green-100 text-green-800",  icon: "⬆️" },
  optimize_price: { label: "Ottimizza prezzo", color: "bg-blue-100 text-blue-800",   icon: "💰" },
  reposition:     { label: "Riposiziona",     color: "bg-yellow-100 text-yellow-800", icon: "↔️" },
  remove:         { label: "Rimuovi",         color: "bg-red-100 text-red-800",      icon: "🗑" },
  monitor:        { label: "Monitora",        color: "bg-gray-100 text-gray-700",    icon: "👀" },
};

const PRIORITY_COLORS: Record<string, string> = {
  high:   "border-l-4 border-red-400",
  medium: "border-l-4 border-yellow-400",
  low:    "border-l-4 border-gray-300",
};

export default function MenuPage() {
  const { activeRestaurant, user } = useAuth();
  const [suggestions, setSuggestions] = useState<MenuSuggestion[]>([]);
  const [metrics, setMetrics] = useState<ProductMetric[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"suggestions" | "metrics">("suggestions");

  const rid = activeRestaurant?.id;
  const plan = user?.plan ?? "starter";
  const canUse = plan === "pro" || plan === "premium";

  async function handleAnalyze() {
    if (!rid) return;
    setLoading(true);
    setError(null);
    try {
      const [sug, met] = await Promise.all([analyzeMenu(rid), fetchMenuMetrics(rid)]);
      setSuggestions(sug.suggestions);
      setMetrics(met.metrics);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Errore");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!rid || !e.target.files?.[0]) return;
    setUploading(true);
    setError(null);
    try {
      await uploadSalesCsv(rid, e.target.files[0]);
      await handleAnalyze();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload fallito");
    } finally {
      setUploading(false);
    }
  }

  if (!canUse) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Ottimizzazione Menu</h2>
        <p className="text-gray-500 mb-6">Disponibile dal piano <strong>Pro</strong> in su.</p>
        <a href="/billing" className="inline-block bg-gray-900 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors">
          Upgrade piano →
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ottimizzazione Menu</h1>
          <p className="text-sm text-gray-500 mt-1">Analisi popolarità e margine per ogni prodotto</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <label className="cursor-pointer text-sm bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50">
            {uploading ? "Caricamento…" : "📤 Carica CSV vendite"}
            <input type="file" accept=".csv" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
          <button
            onClick={handleAnalyze}
            disabled={loading || !rid}
            className="text-sm bg-gray-900 text-white px-4 py-2 rounded-xl hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {loading ? "Analisi…" : "Analizza menu"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>
      )}

      {(suggestions.length > 0 || metrics.length > 0) && (
        <>
          <div className="flex gap-1 p-1 bg-gray-100 rounded-xl w-fit">
            {(["suggestions", "metrics"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`text-sm px-4 py-1.5 rounded-lg transition-colors font-medium ${
                  tab === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {t === "suggestions" ? `Suggerimenti (${suggestions.length})` : `Metriche (${metrics.length})`}
              </button>
            ))}
          </div>

          {tab === "suggestions" && (
            <div className="space-y-3">
              {suggestions.length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-8">Nessun suggerimento disponibile</p>
              ) : suggestions.map((s, i) => {
                const cfg = ACTION_LABELS[s.action];
                return (
                  <div key={i} className={`bg-white rounded-xl p-4 shadow-sm ${PRIORITY_COLORS[s.priority]}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-900">{s.product}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.color}`}>
                            {cfg.icon} {cfg.label}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{s.reason}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-lg font-medium ${
                        s.priority === "high" ? "bg-red-50 text-red-600"
                        : s.priority === "medium" ? "bg-yellow-50 text-yellow-600"
                        : "bg-gray-50 text-gray-500"
                      }`}>
                        {s.priority}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {tab === "metrics" && (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Prodotto</th>
                    <th className="px-4 py-3 text-right">Q.tà totale</th>
                    <th className="px-4 py-3 text-right">Revenue totale</th>
                    <th className="px-4 py-3 text-right">Popolarità</th>
                    <th className="px-4 py-3 text-right">Score revenue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {metrics.map((m, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{m.product}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{m.total_quantity}</td>
                      <td className="px-4 py-3 text-right text-gray-600">€{m.total_revenue.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-1.5">
                            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${m.popularity_score * 100}%` }} />
                          </div>
                          <span className="text-gray-600 w-8">{(m.popularity_score * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-1.5">
                            <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${m.revenue_score * 100}%` }} />
                          </div>
                          <span className="text-gray-600 w-8">{(m.revenue_score * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {suggestions.length === 0 && metrics.length === 0 && !loading && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-3">📊</div>
          <p className="text-sm">Carica i dati di vendita e clicca <strong>Analizza menu</strong></p>
          <p className="text-xs mt-1 text-gray-300">Formato CSV: date, product, quantity, revenue</p>
        </div>
      )}
    </div>
  );
}
