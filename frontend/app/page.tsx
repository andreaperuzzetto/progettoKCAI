"use client";

import { useState } from "react";
import { useAuth } from "./lib/auth-context";
import {
  uploadReviewsCsv,
  uploadReviewsText,
  runAnalysis,
  fetchLatestAnalysis,
  type AnalysisData,
} from "./lib/api";

export default function DashboardPage() {
  const { activeRestaurant, user } = useAuth();
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [running, setRunning] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [error, setError] = useState("");
  const [period, setPeriod] = useState("all");
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState("");

  if (!activeRestaurant) {
    return (
      <EmptyState title="Nessun ristorante">
        <p className="text-gray-500 mb-4">
          Crea il tuo primo ristorante per iniziare.
        </p>
        <p className="text-sm text-gray-400">
          Usa il pulsante &ldquo;+ Ristorante&rdquo; nella barra di navigazione.
        </p>
      </EmptyState>
    );
  }

  async function handleCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !activeRestaurant) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      const r = await uploadReviewsCsv(activeRestaurant.id, file);
      setUploadMsg({ type: "ok", text: `✓ ${r.rows_imported} recensioni importate` });
    } catch (err: unknown) {
      setUploadMsg({ type: "err", text: err instanceof Error ? err.message : "Errore upload" });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handlePasteUpload() {
    if (!activeRestaurant) return;
    const lines = pasteText.split("\n").filter(Boolean);
    if (!lines.length) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      const r = await uploadReviewsText(activeRestaurant.id, lines);
      setUploadMsg({ type: "ok", text: `✓ ${r.rows_imported} recensioni importate` });
      setPasteText("");
      setPasteMode(false);
    } catch (err: unknown) {
      setUploadMsg({ type: "err", text: err instanceof Error ? err.message : "Errore upload" });
    } finally {
      setUploading(false);
    }
  }

  async function handleRunAnalysis() {
    if (!activeRestaurant) return;
    setRunning(true);
    setError("");
    try {
      const result = await runAnalysis(activeRestaurant.id, period);
      setAnalysis(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Analisi fallita");
    } finally {
      setRunning(false);
    }
  }

  async function handleLoadLatest() {
    if (!activeRestaurant) return;
    setRunning(true);
    setError("");
    try {
      const result = await fetchLatestAnalysis(activeRestaurant.id);
      if (result) setAnalysis(result);
      else setError("Nessuna analisi trovata. Carica recensioni e avvia l'analisi.");
    } catch {
      setError("Errore nel caricamento.");
    } finally {
      setRunning(false);
    }
  }

  const isInactive = user?.subscription_status === "inactive";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{activeRestaurant.name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">Dashboard operativa AI</p>
        </div>
        <SubscriptionBadge status={user?.subscription_status ?? "trial"} />
      </div>

      {/* Upload Section */}
      <section className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">📥 Carica Recensioni</h2>
        <div className="flex flex-wrap gap-3 mb-3">
          <label className={`cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${uploading ? "opacity-50 cursor-not-allowed" : "border-gray-300 hover:border-gray-900 hover:bg-gray-50"}`}>
            <span>📄 CSV</span>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              disabled={uploading}
              onChange={handleCsvUpload}
            />
          </label>
          <button
            onClick={() => setPasteMode(!pasteMode)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium hover:border-gray-900 hover:bg-gray-50 transition-colors"
          >
            ✏️ Testo libero
          </button>
        </div>

        {pasteMode && (
          <div className="mt-3">
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              rows={5}
              placeholder={"Una recensione per riga...\nOttimo cibo, servizio veloce.\nServizio lento ma piatti buoni."}
              className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-gray-900 font-mono"
            />
            <div className="flex gap-2 mt-2">
              <button
                onClick={handlePasteUpload}
                disabled={uploading || !pasteText.trim()}
                className="px-4 py-1.5 bg-gray-900 text-white text-sm rounded-lg disabled:opacity-50 hover:bg-gray-700"
              >
                {uploading ? "Caricamento..." : "Importa"}
              </button>
              <button onClick={() => setPasteMode(false)} className="px-4 py-1.5 text-sm text-gray-600 hover:text-gray-900">
                Annulla
              </button>
            </div>
          </div>
        )}

        {uploadMsg && (
          <p className={`mt-3 text-sm px-3 py-2 rounded-lg ${uploadMsg.type === "ok" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
            {uploadMsg.text}
          </p>
        )}
      </section>

      {/* Analysis Controls */}
      <section className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">🔬 Analisi AI</h2>

        {isInactive && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
            Trial scaduto. <a href="/billing" className="underline font-medium">Attiva il piano</a> per eseguire l'analisi.
          </div>
        )}

        <div className="flex flex-wrap gap-3 items-center">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
          >
            <option value="all">Tutte le recensioni</option>
            <option value="last_30_days">Ultimi 30 giorni</option>
          </select>
          <button
            onClick={handleRunAnalysis}
            disabled={running || isInactive}
            className="flex items-center gap-2 px-5 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {running ? (
              <><span className="animate-spin">⟳</span> Analisi in corso...</>
            ) : (
              "▶ Avvia Analisi"
            )}
          </button>
          <button
            onClick={handleLoadLatest}
            disabled={running}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Carica ultima analisi
          </button>
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
        )}
      </section>

      {/* Results */}
      {analysis && <AnalysisResults analysis={analysis} />}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function EmptyState({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="text-center py-20">
      <h2 className="text-xl font-semibold text-gray-900 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function SubscriptionBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; class: string }> = {
    active: { label: "Attivo", class: "bg-green-100 text-green-800" },
    trial: { label: "Trial", class: "bg-blue-100 text-blue-800" },
    inactive: { label: "Scaduto", class: "bg-red-100 text-red-800" },
  };
  const c = config[status] ?? config.inactive;
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${c.class}`}>
      {c.label}
    </span>
  );
}

function AnalysisResults({ analysis }: { analysis: AnalysisData }) {
  const pos = analysis.sentiment.positive_percentage;
  const neg = analysis.sentiment.negative_percentage;
  const neutral = Math.max(0, 100 - pos - neg);
  const date = new Date(analysis.created_at).toLocaleDateString("it-IT", {
    day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <div className="space-y-6">
      <p className="text-xs text-gray-400">Analisi del {date} · periodo: {analysis.period === "all" ? "tutte le recensioni" : "ultimi 30 giorni"}</p>

      {/* Sentiment */}
      <section className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-5">😊 Sentiment</h2>
        <div className="flex gap-4 mb-5">
          <SentimentCard value={pos} label="Positivo" color="green" />
          <SentimentCard value={neg} label="Negativo" color="red" />
          <SentimentCard value={neutral} label="Neutro" color="gray" />
        </div>
        {/* Bar */}
        <div className="h-3 rounded-full overflow-hidden flex bg-gray-100">
          {pos > 0 && <div className="bg-green-400 transition-all" style={{ width: `${pos}%` }} />}
          {neutral > 0 && <div className="bg-gray-300 transition-all" style={{ width: `${neutral}%` }} />}
          {neg > 0 && <div className="bg-red-400 transition-all" style={{ width: `${neg}%` }} />}
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>0%</span><span>100%</span>
        </div>
      </section>

      {/* Issues + Strengths */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">⚠️ Problemi principali</h2>
          {analysis.issues.length > 0 ? (
            <ul className="space-y-3">
              {analysis.issues.map((issue, i) => (
                <IssueRow key={i} name={issue.name} frequency={issue.frequency} color="red" />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">Nessun problema rilevato.</p>
          )}
        </section>

        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">✨ Punti di forza</h2>
          {analysis.strengths.length > 0 ? (
            <ul className="space-y-3">
              {analysis.strengths.map((s, i) => (
                <IssueRow key={i} name={s.name} frequency={s.frequency} color="green" />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">Nessun punto di forza rilevato.</p>
          )}
        </section>
      </div>

      {/* Suggestions */}
      {analysis.suggestions.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">💡 Azioni consigliate</h2>
          <div className="space-y-3">
            {analysis.suggestions.map((s, i) => (
              <div key={i} className="flex gap-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
                <div className="shrink-0 w-6 h-6 bg-gray-900 text-white text-xs rounded-full flex items-center justify-center font-bold">
                  {i + 1}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800 capitalize">{s.problem}</p>
                  <p className="text-sm text-gray-600 mt-0.5">→ {s.action}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function SentimentCard({ value, label, color }: { value: number; label: string; color: "green" | "red" | "gray" }) {
  const colors = {
    green: "bg-green-50 text-green-800",
    red: "bg-red-50 text-red-800",
    gray: "bg-gray-50 text-gray-700",
  };
  return (
    <div className={`flex-1 rounded-xl px-4 py-3 text-center ${colors[color]}`}>
      <div className="text-2xl font-bold">{value}%</div>
      <div className="text-xs mt-0.5 font-medium">{label}</div>
    </div>
  );
}

function IssueRow({ name, frequency, color }: { name: string; frequency: number; color: "red" | "green" }) {
  const badge = color === "red"
    ? "bg-red-100 text-red-700"
    : "bg-green-100 text-green-700";
  return (
    <li className="flex items-center justify-between gap-2">
      <span className="text-sm text-gray-700 capitalize">{name}</span>
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${badge}`}>
        {frequency}×
      </span>
    </li>
  );
}
