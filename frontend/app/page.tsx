"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "./lib/auth-context";
import {
  uploadReviewsCsv, uploadReviewsText, runAnalysis, fetchLatestAnalysis,
  uploadSalesCsv, generateForecast, fetchDailyReport,
  type AnalysisData, type DailyReport, type Suggestion, type AnalysisSuggestion,
} from "./lib/api";
import Link from "next/link";

// ── Priority badge ─────────────────────────────────────────────────────────────
function PriorityBadge({ priority }: { priority: string }) {
  const cls =
    priority === "high" ? "bg-red-100 text-red-700" :
    priority === "medium" ? "bg-amber-100 text-amber-700" :
    "bg-green-100 text-green-700";
  const label = priority === "high" ? "Alta" : priority === "medium" ? "Media" : "Bassa";
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>{label}</span>;
}

// ── Suggestion card ────────────────────────────────────────────────────────────
function SuggestionCard({ s }: { s: Suggestion }) {
  const icon =
    s.type === "staffing" ? "👥" :
    s.type === "inventory" ? "🛒" :
    s.type === "kitchen" ? "🍳" :
    s.type === "menu" ? "📋" :
    s.type === "operations" ? "🧹" :
    "💡";
  return (
    <div className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-xl">
      <span className="text-xl shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 leading-relaxed">{s.message}</p>
      </div>
      <PriorityBadge priority={s.priority} />
    </div>
  );
}

// ── Stat card ──────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const { user, activeRestaurant } = useAuth();
  const [tab, setTab] = useState<"oggi" | "recensioni" | "dati">("oggi");

  // Daily report state
  const [report, setReport] = useState<DailyReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");

  // Analysis state
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisMsg, setAnalysisMsg] = useState("");

  // Upload states
  const [uploadMsg, setUploadMsg] = useState("");
  const [salesMsg, setSalesMsg] = useState("");
  const [reviewText, setReviewText] = useState("");

  const rid = activeRestaurant?.id;

  const loadReport = useCallback(async () => {
    if (!rid) return;
    setReportLoading(true);
    setReportError("");
    try {
      const r = await fetchDailyReport(rid);
      setReport(r);
    } catch {
      setReportError("Previsione non disponibile. Carica dati di vendita e genera la previsione.");
    } finally {
      setReportLoading(false);
    }
  }, [rid]);

  const loadAnalysis = useCallback(async () => {
    if (!rid) return;
    try {
      const r = await fetchLatestAnalysis(rid);
      setAnalysis(r ?? null);
    } catch {}
  }, [rid]);

  useEffect(() => {
    if (rid) {
      loadReport();
      loadAnalysis();
    }
  }, [rid, loadReport, loadAnalysis]);

  // ── Handlers ──────────────────────────────────────────────────────────────────

  async function handleReviewCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !rid) return;
    setUploadMsg("Caricamento…");
    try {
      const r = await uploadReviewsCsv(rid, file);
      setUploadMsg(`✅ ${r.rows_imported} recensioni importate`);
    } catch (err: unknown) {
      setUploadMsg(`❌ ${err instanceof Error ? err.message : "Errore"}`);
    }
  }

  async function handleReviewTextUpload() {
    if (!rid || !reviewText.trim()) return;
    const lines = reviewText.split("\n").map(l => l.trim()).filter(Boolean);
    setUploadMsg("Caricamento…");
    try {
      const r = await uploadReviewsText(rid, lines);
      setUploadMsg(`✅ ${r.rows_imported} recensioni importate`);
      setReviewText("");
    } catch (err: unknown) {
      setUploadMsg(`❌ ${err instanceof Error ? err.message : "Errore"}`);
    }
  }

  async function handleRunAnalysis() {
    if (!rid) return;
    setAnalysisLoading(true);
    setAnalysisMsg("Analisi in corso…");
    try {
      const r = await runAnalysis(rid, "all");
      setAnalysis(r);
      setAnalysisMsg("✅ Analisi completata");
      loadReport(); // refresh report with new issues
    } catch (err: unknown) {
      setAnalysisMsg(`❌ ${err instanceof Error ? err.message : "Errore"}`);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleSalesCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !rid) return;
    setSalesMsg("Caricamento…");
    try {
      const r = await uploadSalesCsv(rid, file);
      setSalesMsg(`✅ ${r.inserted} vendite importate (${r.skipped} duplicate)`);
    } catch (err: unknown) {
      setSalesMsg(`❌ ${err instanceof Error ? err.message : "Errore"}`);
    }
  }

  async function handleGenerateForecast() {
    if (!rid) return;
    setSalesMsg("Generazione previsione…");
    try {
      const r = await generateForecast(rid);
      setSalesMsg(`✅ Previsione generata per ${r.generated} giorni`);
      loadReport();
    } catch (err: unknown) {
      setSalesMsg(`❌ ${err instanceof Error ? err.message : "Errore"}`);
    }
  }

  // ── No restaurant selected ─────────────────────────────────────────────────
  if (!rid) {
    return (
      <div className="text-center py-20">
        <span className="text-5xl">��</span>
        <h2 className="text-xl font-semibold mt-4 text-gray-800">Nessun ristorante selezionato</h2>
        <p className="text-gray-500 mt-2 text-sm">Crea il tuo primo ristorante dal menu in alto.</p>
      </div>
    );
  }

  const isInactive = user?.subscription_status === "inactive";

  // ── Tab: Oggi ──────────────────────────────────────────────────────────────
  const TabOggi = () => (
    <div className="space-y-6">
      {/* Covers + top products */}
      {reportLoading ? (
        <div className="text-center py-12 text-gray-400">Caricamento…</div>
      ) : reportError ? (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          {reportError}
          <div className="mt-3 flex gap-2">
            <button onClick={() => setTab("dati")} className="text-xs bg-amber-700 text-white px-3 py-1.5 rounded-lg hover:bg-amber-800 transition-colors">
              Carica dati vendita →
            </button>
          </div>
        </div>
      ) : report ? (
        <>
          {/* Tomorrow stats */}
          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              📅 Domani — {report.tomorrow.date}
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <StatCard
                label="Coperti attesi"
                value={report.tomorrow.expected_covers}
                sub="previsione AI"
              />
              {report.tomorrow.top_products.slice(0, 2).map(p => (
                <StatCard
                  key={p.name}
                  label={p.name}
                  value={`~${p.predicted_qty}`}
                  sub="pezzi previsti"
                />
              ))}
            </div>
          </div>

          {/* Suggestions */}
          {report.suggestions.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                ✅ Azioni per oggi
              </h2>
              <div className="space-y-2">
                {report.suggestions.map((s, i) => <SuggestionCard key={i} s={s} />)}
              </div>
            </div>
          )}

          {/* 7-day forecast mini table */}
          {report.forecast_7days.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                📈 Previsione 7 giorni
              </h2>
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-4 py-2 text-gray-500 font-medium">Data</th>
                      <th className="text-right px-4 py-2 text-gray-500 font-medium">Coperti</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.forecast_7days.map((f, i) => (
                      <tr key={f.id} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                        <td className="px-4 py-2 text-gray-700">{f.date}</td>
                        <td className="px-4 py-2 text-right font-medium text-gray-900">{f.expected_covers}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Review summary */}
          {report.review_summary.sentiment_positive !== null && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                ⭐ Sentiment recensioni
              </h2>
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="flex gap-4 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-green-400 inline-block" />
                    <span className="text-sm text-gray-700">Positivo: <strong>{Math.round(report.review_summary.sentiment_positive ?? 0)}%</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-red-400 inline-block" />
                    <span className="text-sm text-gray-700">Negativo: <strong>{Math.round(report.review_summary.sentiment_negative ?? 0)}%</strong></span>
                  </div>
                </div>
                {report.review_summary.top_issues.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Problemi principali:</p>
                    <div className="flex flex-wrap gap-2">
                      {report.review_summary.top_issues.map((issue, i) => (
                        <span key={i} className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded-full">
                          {issue.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-gray-400 text-sm">
          Nessun dato disponibile. Carica vendite e recensioni per iniziare.
        </div>
      )}
    </div>
  );

  // ── Tab: Recensioni ────────────────────────────────────────────────────────
  const TabRecensioni = () => (
    <div className="space-y-6">
      {/* Upload CSV */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">📁 Importa da CSV</h3>
        <p className="text-xs text-gray-500 mb-3">Colonne: date, platform, review_text, rating</p>
        <label className="inline-flex items-center gap-2 cursor-pointer bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 transition-colors">
          <span>Scegli file</span>
          <input type="file" accept=".csv" className="hidden" onChange={handleReviewCsvUpload} />
        </label>
      </div>

      {/* Paste text */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">✍️ Incolla recensioni</h3>
        <p className="text-xs text-gray-500 mb-3">Una recensione per riga</p>
        <textarea
          value={reviewText}
          onChange={e => setReviewText(e.target.value)}
          rows={5}
          placeholder={"Ottimo cibo, servizio veloce!\nPiatti freddi, deluso..."}
          className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none"
        />
        <button
          onClick={handleReviewTextUpload}
          disabled={!reviewText.trim()}
          className="mt-2 bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 disabled:opacity-40 transition-colors"
        >
          Importa
        </button>
      </div>

      {uploadMsg && (
        <p className={`text-sm px-3 py-2 rounded-lg ${uploadMsg.startsWith("✅") ? "bg-green-50 text-green-700" : uploadMsg.startsWith("❌") ? "bg-red-50 text-red-700" : "bg-gray-50 text-gray-600"}`}>
          {uploadMsg}
        </p>
      )}

      {/* Analysis */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">🤖 Analisi AI</h3>
        <p className="text-xs text-gray-500 mb-3">Analizza tutte le recensioni e genera insight</p>
        <button
          onClick={handleRunAnalysis}
          disabled={analysisLoading || isInactive}
          className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 disabled:opacity-40 transition-colors"
        >
          {analysisLoading ? "Analisi in corso…" : "Esegui analisi"}
        </button>
        {isInactive && (
          <p className="text-xs text-amber-600 mt-2">
            Piano scaduto. <Link href="/billing" className="underline">Attiva il piano →</Link>
          </p>
        )}
        {analysisMsg && (
          <p className={`text-sm mt-2 ${analysisMsg.startsWith("✅") ? "text-green-600" : analysisMsg.startsWith("❌") ? "text-red-600" : "text-gray-500"}`}>
            {analysisMsg}
          </p>
        )}
      </div>

      {/* Analysis results */}
      {analysis && (
        <div className="space-y-4">
          {/* Sentiment */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h3 className="font-semibold text-gray-800 mb-3">Sentiment</h3>
            <div className="flex gap-6 mb-3 text-sm">
              <span className="text-green-600 font-semibold">✅ {Math.round(analysis.sentiment.positive_percentage)}% positivo</span>
              <span className="text-red-600 font-semibold">❌ {Math.round(analysis.sentiment.negative_percentage)}% negativo</span>
              <span className="text-gray-400">{Math.round(100 - analysis.sentiment.positive_percentage - analysis.sentiment.negative_percentage)}% neutro</span>
            </div>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden flex">
              <div className="bg-green-400 h-full" style={{ width: `${analysis.sentiment.positive_percentage}%` }} />
              <div className="bg-gray-200 h-full" style={{ width: `${100 - analysis.sentiment.positive_percentage - analysis.sentiment.negative_percentage}%` }} />
              <div className="bg-red-400 h-full" style={{ width: `${analysis.sentiment.negative_percentage}%` }} />
            </div>
          </div>

          {/* Issues */}
          {analysis.issues.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-3">⚠️ Problemi ({analysis.issues.length})</h3>
              <div className="space-y-2">
                {analysis.issues.map((issue, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{issue.name}</span>
                    <span className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-full">{issue.frequency}x</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strengths */}
          {analysis.strengths.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-3">💪 Punti di forza ({analysis.strengths.length})</h3>
              <div className="space-y-2">
                {analysis.strengths.map((s, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{s.name}</span>
                    <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">{s.frequency}x</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {analysis.suggestions.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-3">🎯 Suggerimenti operativi</h3>
              <ol className="space-y-3">
                {analysis.suggestions.map((s, i) => (
                  <li key={i} className="flex gap-3 text-sm text-gray-700">
                    <span className="shrink-0 w-6 h-6 bg-gray-100 text-gray-500 rounded-full flex items-center justify-center text-xs font-bold">{i + 1}</span>
                    <div>
                      <span className="font-medium text-gray-900">{s.problem}</span>
                      <span className="text-gray-400 mx-1">→</span>
                      {s.action}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // ── Tab: Dati ──────────────────────────────────────────────────────────────
  const TabDati = () => (
    <div className="space-y-6">
      {/* Sales upload */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">📊 Importa vendite (CSV)</h3>
        <p className="text-xs text-gray-500 mb-3">Colonne richieste: <code className="bg-gray-100 px-1 rounded">date, product, quantity</code> — opzionale: revenue</p>
        <label className="inline-flex items-center gap-2 cursor-pointer bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 transition-colors">
          <span>Scegli file CSV</span>
          <input type="file" accept=".csv" className="hidden" onChange={handleSalesCsvUpload} />
        </label>
      </div>

      {/* Generate forecast */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">🔮 Genera previsione</h3>
        <p className="text-xs text-gray-500 mb-3">Analizza le vendite storiche e prevede i prossimi 7 giorni</p>
        <button
          onClick={handleGenerateForecast}
          className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 transition-colors"
        >
          Genera previsione
        </button>
      </div>

      {salesMsg && (
        <p className={`text-sm px-3 py-2 rounded-lg ${salesMsg.startsWith("✅") ? "bg-green-50 text-green-700" : salesMsg.startsWith("❌") ? "bg-red-50 text-red-700" : "bg-gray-50 text-gray-600"}`}>
          {salesMsg}
        </p>
      )}

      {/* Link to products setup */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <p className="text-sm text-blue-800 font-medium mb-1">🛒 Configura prodotti e ingredienti</p>
        <p className="text-xs text-blue-600">Mappa i tuoi prodotti agli ingredienti per ricevere suggerimenti automatici sulle forniture.</p>
        <Link href="/setup" className="inline-block mt-2 text-xs bg-blue-700 text-white px-3 py-1.5 rounded-lg hover:bg-blue-800 transition-colors">
          Configura →
        </Link>
      </div>
    </div>
  );

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{activeRestaurant?.name}</h1>
        <p className="text-sm text-gray-500 mt-1">Report operativo • {new Date().toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long" })}</p>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 w-fit">
        {(["oggi", "recensioni", "dati"] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors capitalize ${
              tab === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "oggi" ? "📊 Oggi" : t === "recensioni" ? "⭐ Recensioni" : "📈 Dati"}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "oggi" && <TabOggi />}
      {tab === "recensioni" && <TabRecensioni />}
      {tab === "dati" && <TabDati />}
    </div>
  );
}
