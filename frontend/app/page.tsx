"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "./lib/auth-context";
import {
  fetchDailyReport, fetchAlerts, markAlertRead, generateAlerts,
  uploadReviewsCsv, uploadReviewsText, runAnalysis, fetchLatestAnalysis,
  uploadSalesCsv, generateForecast, fetchLatestCorrelation, runCorrelation,
  type DailyReport, type AlertItem, type AnalysisData, type Correlation, type Suggestion,
} from "./lib/api";
import Link from "next/link";

// ── Helpers ───────────────────────────────────────────────────────────────────
const PRIORITY_COLOR = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-green-100 text-green-700 border-green-200",
};
const SEVERITY_ICON = { high: "🔴", medium: "🟡", low: "🟢" };
const TYPE_ICON: Record<string, string> = {
  staffing: "👥", inventory: "🛒", kitchen: "🍳", menu: "📋",
  operations: "🧹", ambiance: "🎵", logistics: "🚗",
};

function Badge({ text, cls }: { text: string; cls: string }) {
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${cls}`}>{text}</span>;
}

function ActionCard({ s }: { s: Suggestion }) {
  const icon = TYPE_ICON[s.type] ?? "💡";
  const color = PRIORITY_COLOR[s.priority] ?? PRIORITY_COLOR.low;
  return (
    <div className="flex items-start gap-3 bg-white border border-gray-100 rounded-xl p-3 shadow-sm">
      <span className="text-xl shrink-0 mt-0.5">{icon}</span>
      <p className="text-sm text-gray-800 leading-snug flex-1">{s.message}</p>
      <Badge text={s.priority === "high" ? "Alta" : s.priority === "medium" ? "Media" : "Bassa"} cls={color} />
    </div>
  );
}

function AlertCard({ alert, onRead }: { alert: AlertItem; onRead: (id: string) => void }) {
  const icon = SEVERITY_ICON[alert.severity] ?? "⚪";
  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border transition-opacity ${alert.read ? "opacity-50 bg-gray-50 border-gray-100" : "bg-white border-gray-200 shadow-sm"}`}>
      <span className="text-lg shrink-0 mt-0.5">{icon}</span>
      <p className="text-sm text-gray-800 leading-snug flex-1">{alert.message}</p>
      {!alert.read && (
        <button onClick={() => onRead(alert.id)} className="text-xs text-gray-400 hover:text-gray-600 shrink-0 underline">
          Letto
        </button>
      )}
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user, activeRestaurant } = useAuth();
  const rid = activeRestaurant?.id;

  // State
  const [report, setReport] = useState<DailyReport | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [correlations, setCorrelations] = useState<Correlation[]>([]);
  const [tab, setTab] = useState<"oggi" | "problemi" | "azioni" | "dati">("oggi");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [reviewText, setReviewText] = useState("");

  const isInactive = user?.subscription_status === "inactive";
  const plan = user?.plan ?? "starter";
  const canForecast = !isInactive;
  const canAlerts = !isInactive;

  const loadAll = useCallback(async () => {
    if (!rid) return;
    setLoading(true);
    try {
      const [r, a, al, corr] = await Promise.allSettled([
        fetchDailyReport(rid),
        fetchLatestAnalysis(rid),
        fetchAlerts(rid),
        fetchLatestCorrelation(rid),
      ]);
      if (r.status === "fulfilled") setReport(r.value);
      if (a.status === "fulfilled") setAnalysis(a.value);
      if (al.status === "fulfilled") { setAlerts(al.value.alerts); setUnread(al.value.unread_count); }
      if (corr.status === "fulfilled") setCorrelations(corr.value.correlations);
    } finally {
      setLoading(false);
    }
  }, [rid]);

  useEffect(() => { loadAll(); }, [loadAll]);

  async function handleMarkRead(alertId: string) {
    if (!rid) return;
    await markAlertRead(rid, alertId);
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, read: true } : a));
    setUnread(prev => Math.max(0, prev - 1));
  }

  async function handleGenerateAlerts() {
    if (!rid) return;
    setMsg("Rilevamento alert…");
    try {
      const r = await generateAlerts(rid);
      setMsg(`✅ ${r.generated} nuovi alert rilevati`);
      loadAll();
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleSalesCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !rid) return;
    setMsg("Caricamento…");
    try {
      const r = await uploadSalesCsv(rid, file);
      setMsg(`✅ ${r.inserted} vendite importate`);
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleGenerateForecast() {
    if (!rid) return;
    setMsg("Generazione previsione…");
    try {
      const r = await generateForecast(rid);
      setMsg(`✅ Previsione aggiornata (${r.generated} giorni)`);
      loadAll();
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleReviewCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !rid) return;
    setMsg("Caricamento…");
    try {
      const r = await uploadReviewsCsv(rid, file);
      setMsg(`✅ ${r.rows_imported} recensioni importate`);
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleTextUpload() {
    if (!rid || !reviewText.trim()) return;
    const lines = reviewText.split("\n").map(l => l.trim()).filter(Boolean);
    setMsg("Caricamento…");
    try {
      const r = await uploadReviewsText(rid, lines);
      setMsg(`✅ ${r.rows_imported} recensioni importate`);
      setReviewText("");
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleRunAnalysis() {
    if (!rid) return;
    setMsg("Analisi in corso…");
    try {
      const r = await runAnalysis(rid, "all");
      setAnalysis(r);
      setMsg("✅ Analisi completata");
      loadAll();
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  async function handleRunCorrelation() {
    if (!rid) return;
    setMsg("Analisi causale in corso…");
    try {
      const r = await runCorrelation(rid);
      setCorrelations(r.correlations);
      setMsg(`✅ ${r.correlations.length} correlazioni trovate`);
    } catch (e: unknown) {
      setMsg(`❌ ${e instanceof Error ? e.message : "Errore"}`);
    }
  }

  if (!rid) {
    return (
      <div className="text-center py-24">
        <span className="text-5xl">🍽</span>
        <h2 className="text-xl font-semibold mt-4 text-gray-800">Nessun ristorante selezionato</h2>
        <p className="text-gray-500 mt-2 text-sm">Crea il tuo primo ristorante dal menu in alto.</p>
      </div>
    );
  }

  const tomorrow = report?.tomorrow;
  const allSuggestions = report?.suggestions ?? [];
  const highSuggestions = allSuggestions.filter(s => s.priority === "high");
  const unreadAlerts = alerts.filter(a => !a.read);

  // ── TAB: OGGI ────────────────────────────────────────────────────────────────
  const TabOggi = () => (
    <div className="space-y-6">
      {/* Alert banner */}
      {unreadAlerts.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-red-800 mb-2">🔔 {unreadAlerts.length} alert attivi</p>
          <div className="space-y-2">
            {unreadAlerts.slice(0, 2).map(a => (
              <AlertCard key={a.id} alert={a} onRead={handleMarkRead} />
            ))}
            {unreadAlerts.length > 2 && (
              <button onClick={() => setTab("problemi")} className="text-xs text-red-600 underline">
                Vedi tutti gli alert →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Tomorrow forecast */}
      {tomorrow && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            📅 Domani — {tomorrow.date}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
              <p className="text-3xl font-bold text-gray-900">{tomorrow.expected_covers}</p>
              <p className="text-xs text-gray-500 mt-1">coperti attesi</p>
            </div>
            {tomorrow.top_products.slice(0, 2).map(p => (
              <div key={p.name} className="bg-white border border-gray-200 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">~{p.predicted_qty}</p>
                <p className="text-xs text-gray-500 mt-1">{p.name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top actions (high priority only) */}
      {highSuggestions.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            ⚡ Da fare oggi
          </h2>
          <div className="space-y-2">
            {highSuggestions.slice(0, 3).map((s, i) => <ActionCard key={i} s={s} />)}
          </div>
          {allSuggestions.length > highSuggestions.length && (
            <button onClick={() => setTab("azioni")} className="text-xs text-gray-400 underline mt-2">
              Vedi tutte le azioni →
            </button>
          )}
        </div>
      )}

      {/* Review sentiment pill */}
      {report?.review_summary?.sentiment_positive != null && (
        <div className="flex items-center gap-3 bg-white border border-gray-200 rounded-xl p-4">
          <span className="text-2xl">⭐</span>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {Math.round(report.review_summary.sentiment_positive)}% recensioni positive
            </p>
            {report.review_summary.top_issues.length > 0 && (
              <p className="text-xs text-gray-500 mt-0.5">
                Problemi: {report.review_summary.top_issues.map(i => i.name).join(", ")}
              </p>
            )}
          </div>
          <button onClick={() => setTab("problemi")} className="ml-auto text-xs text-gray-400 underline">
            Dettaglio →
          </button>
        </div>
      )}

      {loading && !report && (
        <div className="text-center py-12 text-gray-400 text-sm">Caricamento…</div>
      )}

      {!loading && !report && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 text-center">
          <p className="text-sm font-medium text-blue-800 mb-2">Nessun dato ancora</p>
          <p className="text-xs text-blue-600 mb-3">Carica le vendite e genera la previsione per vedere i dati di domani.</p>
          <button onClick={() => setTab("dati")} className="text-xs bg-blue-700 text-white px-3 py-1.5 rounded-lg hover:bg-blue-800 transition-colors">
            Vai a Dati →
          </button>
        </div>
      )}
    </div>
  );

  // ── TAB: PROBLEMI ──────────────────────────────────────────────────────────
  const TabProblemi = () => (
    <div className="space-y-6">
      {/* All alerts */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">🔔 Alert</h2>
          <button onClick={handleGenerateAlerts} className="text-xs text-gray-400 underline hover:text-gray-600">
            Rileva nuovi
          </button>
        </div>
        {alerts.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">Nessun alert. Il sistema monitora automaticamente.</p>
        ) : (
          <div className="space-y-2">
            {alerts.slice(0, 10).map(a => <AlertCard key={a.id} alert={a} onRead={handleMarkRead} />)}
          </div>
        )}
      </div>

      {/* Review issues */}
      {analysis && analysis.issues.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            ⚠️ Problemi nelle recensioni
          </h2>
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {analysis.issues.map((issue, i) => (
              <div key={i} className={`flex items-center justify-between px-4 py-3 ${i > 0 ? "border-t border-gray-100" : ""}`}>
                <span className="text-sm text-gray-800">{issue.name}</span>
                <span className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-full">{issue.frequency}x</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Correlations (causal analysis) */}
      {correlations.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">🔍 Analisi causale</h2>
            <button onClick={handleRunCorrelation} className="text-xs text-gray-400 underline">Aggiorna</button>
          </div>
          <div className="space-y-3">
            {correlations.map((c, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Causa:</span>
                  <span className="text-sm text-gray-900">{c.cause}</span>
                  <span className="ml-auto text-xs text-gray-400">{Math.round(c.confidence * 100)}% confidenza</span>
                </div>
                <p className="text-sm text-gray-700 leading-snug">{c.suggestion}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!analysis && correlations.length === 0 && (
        <div className="text-center py-10">
          <p className="text-sm text-gray-400">Carica recensioni e avvia l'analisi per vedere i problemi.</p>
          <button onClick={() => setTab("dati")} className="mt-3 text-xs text-gray-500 underline">Vai a Dati →</button>
        </div>
      )}
    </div>
  );

  // ── TAB: AZIONI ────────────────────────────────────────────────────────────
  const TabAzioni = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">✅ Tutte le azioni suggerite</h2>
        <span className="text-xs text-gray-400">{allSuggestions.length} azioni</span>
      </div>

      {allSuggestions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-gray-400">Nessuna azione suggerita. Aggiorna i dati di vendita e la previsione.</p>
          <button onClick={() => setTab("dati")} className="mt-3 text-xs text-gray-500 underline">Vai a Dati →</button>
        </div>
      ) : (
        <>
          {allSuggestions.map((s, i) => <ActionCard key={i} s={s} />)}

          {/* Run correlation button */}
          <div className="pt-2 border-t border-gray-100">
            <button
              onClick={handleRunCorrelation}
              className="text-sm text-gray-600 hover:text-gray-900 underline"
            >
              🔍 Esegui analisi causale avanzata
            </button>
            <p className="text-xs text-gray-400 mt-0.5">
              Combina dati vendite + recensioni per trovare le cause dei problemi
            </p>
          </div>
        </>
      )}
    </div>
  );

  // ── TAB: DATI ──────────────────────────────────────────────────────────────
  const TabDati = () => (
    <div className="space-y-6">
      {/* Sales upload */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">📊 Importa vendite</h3>
        <p className="text-xs text-gray-500 mb-3">CSV con colonne: <code className="bg-gray-100 px-1 rounded">date, product, quantity</code></p>
        <label className="inline-flex cursor-pointer bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 transition-colors">
          Scegli file CSV
          <input type="file" accept=".csv" className="hidden" onChange={handleSalesCsvUpload} />
        </label>
      </div>

      {/* Forecast */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">🔮 Genera previsione</h3>
        <p className="text-xs text-gray-500 mb-3">Analizza le vendite storiche e prevede i prossimi 7 giorni</p>
        <button onClick={handleGenerateForecast} disabled={!canForecast} className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 disabled:opacity-40 transition-colors">
          Genera previsione
        </button>
      </div>

      {/* Reviews */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">⭐ Importa recensioni</h3>
        <div className="flex gap-2 mb-3">
          <label className="inline-flex cursor-pointer text-xs border border-gray-300 text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
            CSV
            <input type="file" accept=".csv" className="hidden" onChange={handleReviewCsvUpload} />
          </label>
        </div>
        <textarea
          value={reviewText}
          onChange={e => setReviewText(e.target.value)}
          rows={4}
          placeholder={"Incolla recensioni — una per riga\n\nOttimo cibo!\nServizio lento purtroppo..."}
          className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none"
        />
        <div className="flex items-center gap-3 mt-2">
          <button onClick={handleTextUpload} disabled={!reviewText.trim()} className="text-sm bg-gray-900 text-white px-3 py-1.5 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors">
            Importa
          </button>
          <button onClick={handleRunAnalysis} disabled={isInactive} className="text-sm border border-gray-300 text-gray-700 px-3 py-1.5 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors">
            🤖 Analizza
          </button>
          {isInactive && <Link href="/billing" className="text-xs text-amber-600 underline">Attiva piano →</Link>}
        </div>
      </div>

      {/* Setup link */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <p className="text-sm font-medium text-blue-800">🛒 Prodotti e ingredienti</p>
        <p className="text-xs text-blue-600 mt-0.5">Mappa i prodotti agli ingredienti per suggerimenti automatici sulle forniture.</p>
        <Link href="/setup" className="inline-block mt-2 text-xs bg-blue-700 text-white px-3 py-1.5 rounded-lg hover:bg-blue-800 transition-colors">
          Configura →
        </Link>
      </div>

      {/* Integrations link */}
      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-1">
          <p className="text-sm font-medium text-purple-800">⚡ Integrazioni automatiche</p>
          {plan !== "premium" && <Badge text="Premium" cls="bg-purple-100 text-purple-700 border-purple-200" />}
        </div>
        <p className="text-xs text-purple-600">Connetti il tuo POS (Square, Toast) per importare le vendite automaticamente ogni ora.</p>
        {plan === "premium" ? (
          <Link href="/integrations" className="inline-block mt-2 text-xs bg-purple-700 text-white px-3 py-1.5 rounded-lg hover:bg-purple-800 transition-colors">
            Gestisci integrazioni →
          </Link>
        ) : (
          <Link href="/billing" className="inline-block mt-2 text-xs bg-purple-700 text-white px-3 py-1.5 rounded-lg hover:bg-purple-800 transition-colors">
            Passa a Premium →
          </Link>
        )}
      </div>
    </div>
  );

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{activeRestaurant?.name}</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {new Date().toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long" })}
          </p>
        </div>
        {unread > 0 && (
          <button onClick={() => setTab("problemi")} className="flex items-center gap-1.5 bg-red-500 text-white text-xs font-medium px-3 py-1.5 rounded-full hover:bg-red-600 transition-colors">
            🔔 {unread} alert
          </button>
        )}
      </div>

      {/* Status message */}
      {msg && (
        <div className={`text-sm px-3 py-2 rounded-lg mb-4 ${msg.startsWith("✅") ? "bg-green-50 text-green-700" : msg.startsWith("❌") ? "bg-red-50 text-red-700" : "bg-gray-50 text-gray-600"}`}>
          {msg}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 w-fit">
        {[
          { id: "oggi", label: "📊 Oggi" },
          { id: "problemi", label: unread > 0 ? `⚠️ Problemi (${unread})` : "⚠️ Problemi" },
          { id: "azioni", label: "✅ Azioni" },
          { id: "dati", label: "📈 Dati" },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as typeof tab)}
            className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${tab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "oggi" && <TabOggi />}
      {tab === "problemi" && <TabProblemi />}
      {tab === "azioni" && <TabAzioni />}
      {tab === "dati" && <TabDati />}
    </div>
  );
}
