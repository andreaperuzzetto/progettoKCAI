"use client";

import { useState } from "react";
import { fetchCorrelation } from "../lib/api";

const DEMO_RESTAURANT_ID = "00000000-0000-0000-0000-000000000001";

interface Hypothesis {
  problem: string;
  possible_cause: string;
  suggested_action: string;
  spike_detected: boolean;
}

export default function OpportunitiesPage() {
  const [data, setData] = useState<{ hypotheses: Hypothesis[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLoad() {
    setLoading(true);
    setError("");
    try {
      const result = await fetchCorrelation(DEMO_RESTAURANT_ID);
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Opportunities</h1>

      <button
        onClick={handleLoad}
        disabled={loading}
        className="bg-gray-900 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50 mb-6"
      >
        {loading ? "Loading..." : "Find Opportunities"}
      </button>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {data && (
        <div className="space-y-4">
          {data.hypotheses.length > 0 ? (
            data.hypotheses.map((h, i) => (
              <div key={i} className="border rounded p-4">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold capitalize">{h.problem}</h3>
                  {h.spike_detected && (
                    <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded">
                      Order spike detected
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium">Cause:</span> {h.possible_cause}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Action:</span>{" "}
                  {h.suggested_action}
                </p>
              </div>
            ))
          ) : (
            <p className="text-gray-500">
              No operational insights detected. Upload more data to improve
              analysis.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
