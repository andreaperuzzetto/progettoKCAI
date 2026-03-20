"use client";

import { useState } from "react";
import { useAuth } from "../lib/auth-context";
import {
  generatePurchaseOrder,
  fetchStaffPlan,
  PurchaseOrderItem,
  StaffShift,
} from "../lib/api";

export default function OperationsPage() {
  const { activeRestaurant, user } = useAuth();
  const [orderItems, setOrderItems] = useState<PurchaseOrderItem[]>([]);
  const [shifts, setShifts] = useState<StaffShift[]>([]);
  const [generatingOrder, setGeneratingOrder] = useState(false);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);
  const [staffError, setStaffError] = useState<string | null>(null);
  const [orderGeneratedAt, setOrderGeneratedAt] = useState<string | null>(null);
  const [tab, setTab] = useState<"order" | "staff">("order");

  const rid = activeRestaurant?.id;
  const plan = user?.plan ?? "starter";
  const canUse = plan === "premium";

  async function handleGenerateOrder() {
    if (!rid) return;
    setGeneratingOrder(true);
    setOrderError(null);
    try {
      const result = await generatePurchaseOrder(rid);
      setOrderItems(result.items);
      setOrderGeneratedAt(result.generated_at);
    } catch (e: unknown) {
      setOrderError(e instanceof Error ? e.message : "Errore");
    } finally {
      setGeneratingOrder(false);
    }
  }

  async function handleLoadStaff() {
    if (!rid) return;
    setLoadingStaff(true);
    setStaffError(null);
    try {
      const result = await fetchStaffPlan(rid);
      setShifts(result.shifts);
    } catch (e: unknown) {
      setStaffError(e instanceof Error ? e.message : "Errore");
    } finally {
      setLoadingStaff(false);
    }
  }

  if (!canUse) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Automazione Operativa</h2>
        <p className="text-gray-500 mb-6">Disponibile solo nel piano <strong>Premium</strong>.</p>
        <a href="/billing" className="inline-block bg-gray-900 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors">
          Upgrade a Premium →
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Automazione Operativa</h1>
        <p className="text-sm text-gray-500 mt-1">Ordini d'acquisto automatici e pianificazione staff</p>
      </div>

      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl w-fit">
        {(["order", "staff"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`text-sm px-4 py-1.5 rounded-lg transition-colors font-medium ${
              tab === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "order" ? "📦 Ordini acquisti" : "👥 Piano staff"}
          </button>
        ))}
      </div>

      {tab === "order" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">Ordine d'acquisto</h2>
              <p className="text-xs text-gray-400 mt-0.5">Generato dal forecast dei prossimi 7 giorni</p>
            </div>
            <button
              onClick={handleGenerateOrder}
              disabled={generatingOrder || !rid}
              className="text-sm bg-gray-900 text-white px-4 py-2 rounded-xl hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {generatingOrder ? "Generazione…" : "Genera ordine"}
            </button>
          </div>

          {orderError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{orderError}</div>
          )}

          {orderItems.length > 0 ? (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              {orderGeneratedAt && (
                <div className="px-4 py-2 border-b border-gray-100 text-xs text-gray-400">
                  Generato: {new Date(orderGeneratedAt).toLocaleString("it-IT")}
                </div>
              )}
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Ingrediente</th>
                    <th className="px-4 py-3 text-right">Quantità</th>
                    <th className="px-4 py-3 text-left">Unità</th>
                    <th className="px-4 py-3 text-left">Fornitore</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {orderItems.map((item, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{item.ingredient}</td>
                      <td className="px-4 py-3 text-right text-gray-700">{item.quantity}</td>
                      <td className="px-4 py-3 text-gray-500">{item.unit}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{item.suggested_supplier ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : !generatingOrder && (
            <div className="text-center py-12 text-gray-400">
              <div className="text-4xl mb-3">📦</div>
              <p className="text-sm">Clicca <strong>Genera ordine</strong> per calcolare gli acquisti necessari</p>
            </div>
          )}
        </div>
      )}

      {tab === "staff" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">Piano staff prossimi 7 giorni</h2>
              <p className="text-xs text-gray-400 mt-0.5">Basato sul forecast della domanda</p>
            </div>
            <button
              onClick={handleLoadStaff}
              disabled={loadingStaff || !rid}
              className="text-sm bg-gray-900 text-white px-4 py-2 rounded-xl hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {loadingStaff ? "Caricamento…" : "Carica piano"}
            </button>
          </div>

          {staffError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{staffError}</div>
          )}

          {shifts.length > 0 ? (
            <div className="space-y-2">
              {shifts.map((shift, i) => (
                <div key={i} className="bg-white rounded-xl p-4 shadow-sm flex items-center gap-4">
                  <div className="w-20 shrink-0 text-center">
                    <div className="font-bold text-gray-900">{shift.day_of_week}</div>
                    <div className="text-xs text-gray-400">{new Date(shift.date).toLocaleDateString("it-IT", { day: "numeric", month: "short" })}</div>
                  </div>
                  <div className="flex-1 flex items-center gap-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{shift.expected_covers}</div>
                      <div className="text-xs text-gray-400">coperti previsti</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${
                        shift.recommended_staff >= 6 ? "text-red-600"
                        : shift.recommended_staff >= 4 ? "text-yellow-600"
                        : "text-green-600"
                      }`}>{shift.recommended_staff}</div>
                      <div className="text-xs text-gray-400">staff consigliato</div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-500 italic">{shift.shift_notes}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : !loadingStaff && (
            <div className="text-center py-12 text-gray-400">
              <div className="text-4xl mb-3">👥</div>
              <p className="text-sm">Clicca <strong>Carica piano</strong> per vedere il fabbisogno staff</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
