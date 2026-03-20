"use client";

import { useState } from "react";
import { fetchDailyReport, uploadSales, uploadReviews } from "./lib/api";
import { useAuth } from "./lib/auth-context";

export default function TodayPage() {
  const { activeRestaurant } = useAuth();
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadMsg, setUploadMsg] = useState("");

  async function handleGenerateReport() {
    if (!activeRestaurant) return;
    setLoading(true);
    setError("");
    try {
      const today = new Date().toISOString().split("T")[0];
      const data = await fetchDailyReport(activeRestaurant.id, today);
      setReport(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to generate report");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(
    type: "sales" | "reviews",
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    if (!activeRestaurant) return;
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadMsg("");
    try {
      const fn = type === "sales" ? uploadSales : uploadReviews;
      const result = await fn(activeRestaurant.id, file);
      setUploadMsg(`${type}: ${result.rows_imported} rows imported.`);
    } catch {
      setUploadMsg(`Failed to upload ${type}.`);
    }
    e.target.value = "";
  }

  const forecast = report?.forecast as Record<string, number> | undefined;

  if (!activeRestaurant) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Today</h1>
        <p className="text-gray-500">
          No restaurant found. Use the &quot;+ Restaurant&quot; button in the navigation to create one.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Today</h1>

      <section className="mb-8 flex gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Upload Sales CSV</label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => handleUpload("sales", e)}
            className="text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Upload Reviews CSV</label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => handleUpload("reviews", e)}
            className="text-sm"
          />
        </div>
      </section>

      {uploadMsg && (
        <p className="mb-4 text-sm text-green-700 bg-green-50 px-3 py-2 rounded">
          {uploadMsg}
        </p>
      )}

      <button
        onClick={handleGenerateReport}
        disabled={loading}
        className="bg-gray-900 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50 mb-6"
      >
        {loading ? "Generating..." : "Generate Daily Report"}
      </button>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {report && (
        <div className="space-y-6">
          <div className="border rounded p-4">
            <h2 className="font-semibold text-lg mb-3">Forecast</h2>
            {forecast && Object.keys(forecast).length > 0 ? (
              <ul className="space-y-1">
                {Object.entries(forecast).map(([product, qty]) => (
                  <li key={product} className="flex justify-between max-w-xs">
                    <span className="capitalize">{product}</span>
                    <span className="font-mono">{qty}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No forecast data available.</p>
            )}
          </div>

          <div className="border rounded p-4">
            <h2 className="font-semibold text-lg mb-3">Issues</h2>
            <pre className="text-sm whitespace-pre-wrap text-gray-700">
              {report.issues as string}
            </pre>
          </div>

          <div className="border rounded p-4">
            <h2 className="font-semibold text-lg mb-3">Suggestions</h2>
            <pre className="text-sm whitespace-pre-wrap text-gray-700">
              {report.suggestions as string}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
