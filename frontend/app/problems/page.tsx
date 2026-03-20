"use client";

import { useState } from "react";
import { fetchReviewAnalysis } from "../lib/api";
import { useAuth } from "../lib/auth-context";

export default function ProblemsPage() {
  const { activeRestaurant } = useAuth();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLoad() {
    if (!activeRestaurant) return;
    setLoading(true);
    setError("");
    try {
      const result = await fetchReviewAnalysis(activeRestaurant.id);
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  const sentiments = data?.sentiments as Record<string, number> | undefined;
  const topics = data?.topics as Record<string, number> | undefined;

  if (!activeRestaurant) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Problems</h1>
        <p className="text-gray-500">No restaurant selected.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Problems</h1>

      <button
        onClick={handleLoad}
        disabled={loading}
        className="bg-gray-900 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50 mb-6"
      >
        {loading ? "Loading..." : "Analyze Reviews"}
      </button>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {data && (
        <div className="space-y-6">
          <div className="border rounded p-4">
            <h2 className="font-semibold text-lg mb-3">Sentiment Overview</h2>
            {sentiments && Object.keys(sentiments).length > 0 ? (
              <div className="flex gap-4">
                {Object.entries(sentiments).map(([sentiment, count]) => (
                  <div
                    key={sentiment}
                    className={`px-4 py-3 rounded text-center min-w-24 ${
                      sentiment === "positive"
                        ? "bg-green-50 text-green-800"
                        : sentiment === "negative"
                        ? "bg-red-50 text-red-800"
                        : "bg-gray-50 text-gray-800"
                    }`}
                  >
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-sm capitalize">{sentiment}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No reviews analyzed yet.</p>
            )}
          </div>

          <div className="border rounded p-4">
            <h2 className="font-semibold text-lg mb-3">Recurring Complaints</h2>
            {topics && Object.keys(topics).length > 0 ? (
              <ul className="space-y-2">
                {Object.entries(topics).map(([topic, count]) => (
                  <li
                    key={topic}
                    className="flex justify-between items-center max-w-md"
                  >
                    <span className="capitalize">{topic}</span>
                    <span className="bg-red-100 text-red-800 text-sm px-2 py-0.5 rounded">
                      {count} mention{count > 1 ? "s" : ""}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No complaint topics detected.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
