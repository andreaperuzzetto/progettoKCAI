"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../lib/auth-context";
import { listIntegrations, createIntegration, syncIntegration } from "../lib/api";
import Link from "next/link";

interface Integration {
  id: string;
  provider: string;
  status: string;
  last_sync_at: string | null;
}

const PROVIDERS = [
  { id: "square", name: "Square POS", icon: "🟦", desc: "Importa vendite automaticamente ogni ora" },
  { id: "csv_auto", name: "CSV automatico", icon: "📄", desc: "Monitora una cartella per nuovi file CSV" },
];

const STATUS_COLOR: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  error: "bg-red-100 text-red-700",
  pending: "bg-amber-100 text-amber-700",
};

export default function IntegrationsPage() {
  const { user, activeRestaurant } = useAuth();
  const rid = activeRestaurant?.id;
  const isPremium = user?.plan === "premium";

  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [adding, setAdding] = useState<string | null>(null);
  const [config, setConfig] = useState<Record<string, string>>({});
  const [syncing, setSyncing] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!rid || !isPremium) return;
    setLoading(true);
    try {
      const res = await listIntegrations(rid);
      setIntegrations(res);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [rid, isPremium]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(providerId: string) {
    if (!rid) return;
    setMsg("Creazione integrazione…");
    try {
      await createIntegration(rid, providerId, config);
      setMsg("✅ Integrazione creata");
      setAdding(null);
      setConfig({});
      load();
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleSync(integrationId: string) {
    if (!rid) return;
    setSyncing(integrationId);
    setMsg("Sincronizzazione…");
    try {
      const r = await syncIntegration(rid, integrationId);
      setMsg(`✅ ${r.imported ?? 0} record importati`);
      load();
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore sync"}`);
    } finally {
      setSyncing(null);
    }
  }

  if (!isPremium) {
    return (
      <div className="max-w-xl mx-auto text-center py-24">
        <span className="text-5xl">⚡</span>
        <h2 className="text-xl font-bold text-gray-800 mt-4">Funzione Premium</h2>
        <p className="text-gray-500 text-sm mt-2 mb-6">
          Le integrazioni automatiche con POS sono disponibili nel piano Premium (199€/mese).
        </p>
        <Link href="/billing" className="bg-gray-900 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors">
          Passa a Premium →
        </Link>
      </div>
    );
  }

  const activeProviderIds = integrations.map(i => i.provider);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrazioni</h1>
          <p className="text-sm text-gray-400 mt-0.5">Connetti le tue fonti dati per importazioni automatiche</p>
        </div>
        <Link href="/" className="text-xs text-gray-400 underline hover:text-gray-600">← Dashboard</Link>
      </div>

      {msg && (
        <div className={`text-sm px-3 py-2 rounded-lg mb-4 ${msg.startsWith("✅") ? "bg-green-50 text-green-700" : msg.startsWith("❌") ? "bg-red-50 text-red-700" : "bg-gray-50 text-gray-600"}`}>
          {msg}
        </div>
      )}

      {/* Active integrations */}
      {integrations.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Attive</h2>
          <div className="space-y-3">
            {integrations.map(intg => {
              const provider = PROVIDERS.find(p => p.id === intg.provider);
              return (
                <div key={intg.id} className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4">
                  <span className="text-2xl">{provider?.icon ?? "🔌"}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{provider?.name ?? intg.provider}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {intg.last_sync_at
                        ? `Ultima sync: ${new Date(intg.last_sync_at).toLocaleString("it-IT")}`
                        : "Mai sincronizzata"}
                    </p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[intg.status] ?? "bg-gray-100 text-gray-600"}`}>
                    {intg.status}
                  </span>
                  <button
                    onClick={() => handleSync(intg.id)}
                    disabled={syncing === intg.id}
                    className="text-xs border border-gray-300 text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
                  >
                    {syncing === intg.id ? "…" : "Sync ora"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Available providers */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Disponibili</h2>
        <div className="space-y-3">
          {PROVIDERS.filter(p => !activeProviderIds.includes(p.id)).map(provider => (
            <div key={provider.id} className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{provider.icon}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{provider.name}</p>
                  <p className="text-xs text-gray-400">{provider.desc}</p>
                </div>
                <button
                  onClick={() => setAdding(adding === provider.id ? null : provider.id)}
                  className="text-xs bg-gray-900 text-white px-3 py-1.5 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  {adding === provider.id ? "Annulla" : "Connetti"}
                </button>
              </div>

              {adding === provider.id && (
                <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
                  {provider.id === "square" && (
                    <input
                      type="text"
                      placeholder="Square Access Token"
                      value={config.api_key ?? ""}
                      onChange={e => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                    />
                  )}
                  {provider.id === "csv_auto" && (
                    <input
                      type="text"
                      placeholder="Percorso cartella (es. /uploads/restaurant1)"
                      value={config.folder_path ?? ""}
                      onChange={e => setConfig(prev => ({ ...prev, folder_path: e.target.value }))}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                    />
                  )}
                  <button
                    onClick={() => handleCreate(provider.id)}
                    className="text-sm bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Salva e connetti
                  </button>
                </div>
              )}
            </div>
          ))}

          {PROVIDERS.every(p => activeProviderIds.includes(p.id)) && (
            <p className="text-sm text-gray-400 text-center py-8">
              Tutte le integrazioni disponibili sono già attive.
            </p>
          )}
        </div>
      </div>

      {loading && integrations.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-12">Caricamento…</p>
      )}
    </div>
  );
}
