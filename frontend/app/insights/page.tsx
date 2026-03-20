"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth-context";
import { generateInsights, fetchLatestInsights, markInsightRead, InsightItem } from "../lib/api";

function confidenceBar(v: number) {
  const pct = Math.round(v * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-gray-200 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${v >= 0.7 ? "bg-green-500" : v >= 0.4 ? "bg-yellow-400" : "bg-red-400"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8">{pct}%</span>
    </div>
  );
}

const TYPE_ICONS: Record<string, string> = {
  high_demand:       "📈",
  low_sentiment:     "⚠️",
  sales_anomaly:     "🔍",
  review_spike:      "💬",
  demand_drop:       "📉",
  quality_issue:     "🍽",
  predictive:        "🔮",
  diagnostic:        "🩺",
  prescriptive:      "💡",
};

export default function InsightsPage() {
  const { activeRestaurant, user } = useAuth();
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rid = activeRestaurant?.id;
  const plan = user?.plan ?? "starter";
  const canUse = plan === "pro" || plan === "premium";

  useEffect(() => {
    if (!rid || !canUse) return;
    loadInsights();
  }, [rid]);

  async function loadInsights() {
    if (!rid) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchLatestInsights(rid);
      setInsights(result.insights);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Errore");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    if (!rid) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await generateInsights(rid);
      setInsights(result.insights);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Errore");
    } finally {
      setGenerating(false);
    }
  }

  async function handleMarkRead(insightId: string) {
    if (!rid) return;
    try {
      await markInsightRead(rid, insightId);
      setInsights((prev) =>
        prev.map((ins) =>
          ins.id === insightId ? { ...ins, read_at: new Date().toISOString() } : ins
        )
      );
    } catch { /* ignore */ }
  }

  if (!canUse) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Insights Proattivi</h2>
        <p className="text-gray-500 mb-6">Disponibile dal piano <strong>Pro</strong> in su.</p>
        <a href="/billing" className="inline-block bg-gray-900 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors">
          Upgrade piano →
        </a>
      </div>
    );
  }

  const unread = insights.filter((i) => !i.read_at);
  const read = insights.filter((i) => i.read_at);

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Insights Proattivi</h1>
          <p className="text-sm text-gray-500 mt-1">Il sistema osserva continuamente e ti avvisa</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating || !rid}
          className="text-sm bg-gray-900 text-white px-4 py-2 rounded-xl hover:bg-gray-700 transition-colors disabled:opacity-50"
        >
          {generating ? "Analisi…" : "Genera insights"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>
      )}

      {loading && (
        <div className="text-center py-12 text-gray-400 text-sm">Caricamento…</div>
      )}

      {!loading && insights.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-3">🔮</div>
          <p className="text-sm">Clicca <strong>Genera insights</strong> per avviare l'analisi</p>
          <p className="text-xs mt-1 text-gray-300">Il sistema analizza vendite, recensioni e trend</p>
        </div>
      )}

      {unread.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Nuovi ({unread.length})
          </h2>
          {unread.map((insight) => (
            <InsightCard key={insight.id} insight={insight} onRead={() => handleMarkRead(insight.id)} />
          ))}
        </div>
      )}

      {read.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
            Letti ({read.length})
          </h2>
          {read.map((insight) => (
            <InsightCard key={insight.id} insight={insight} dimmed />
          ))}
        </div>
      )}
    </div>
  );
}

function InsightCard({
  insight,
  onRead,
  dimmed = false,
}: {
  insight: InsightItem;
  onRead?: () => void;
  dimmed?: boolean;
}) {
  const icon = TYPE_ICONS[insight.type] ?? "💡";
  const score = insight.confidence * insight.impact;
  const impactColor = score >= 0.6 ? "border-l-4 border-red-400" : score >= 0.3 ? "border-l-4 border-yellow-400" : "border-l-4 border-gray-200";

  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm transition-opacity ${impactColor} ${dimmed ? "opacity-50" : ""}`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`text-sm ${dimmed ? "text-gray-500" : "text-gray-800 font-medium"}`}>{insight.message}</p>
            {!insight.read_at && onRead && (
              <button
                onClick={onRead}
                className="text-xs text-gray-400 hover:text-gray-700 shrink-0 underline"
              >
                Letto
              </button>
            )}
          </div>
          <div className="flex items-center gap-4 mt-2">
            <div>
              <div className="text-xs text-gray-400 mb-0.5">Confidenza</div>
              {confidenceBar(insight.confidence)}
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-0.5">Impatto</div>
              {confidenceBar(insight.impact)}
            </div>
            <div className="ml-auto">
              <span className="text-xs text-gray-300">
                {new Date(insight.created_at).toLocaleDateString("it-IT")}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
