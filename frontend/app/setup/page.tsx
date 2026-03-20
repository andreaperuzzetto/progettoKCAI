"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../lib/auth-context";
import { authHeaders } from "../lib/api";

const API_BASE = "http://localhost:8000";

interface Product { id: string; name: string; category: string | null; ingredients: { ingredient_id: string; quantity_per_unit: number }[] }
interface Ingredient { id: string; name: string; unit: string | null }

export default function SetupPage() {
  const { activeRestaurant } = useAuth();
  const rid = activeRestaurant?.id;

  const [products, setProducts] = useState<Product[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [newProduct, setNewProduct] = useState({ name: "", category: "" });
  const [newIngredient, setNewIngredient] = useState({ name: "", unit: "" });
  const [msg, setMsg] = useState("");

  const loadData = useCallback(async () => {
    if (!rid) return;
    const [p, i] = await Promise.all([
      fetch(`${API_BASE}/products?restaurant_id=${rid}`, { headers: authHeaders() }).then(r => r.json()),
      fetch(`${API_BASE}/ingredients?restaurant_id=${rid}`, { headers: authHeaders() }).then(r => r.json()),
    ]);
    setProducts(p);
    setIngredients(i);
  }, [rid]);

  useEffect(() => { loadData(); }, [loadData]);

  async function createProduct() {
    if (!rid || !newProduct.name.trim()) return;
    await fetch(`${API_BASE}/products?restaurant_id=${rid}`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ name: newProduct.name, category: newProduct.category || null }),
    });
    setNewProduct({ name: "", category: "" });
    setMsg("✅ Prodotto creato");
    loadData();
  }

  async function createIngredient() {
    if (!rid || !newIngredient.name.trim()) return;
    await fetch(`${API_BASE}/ingredients?restaurant_id=${rid}`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ name: newIngredient.name, unit: newIngredient.unit || null }),
    });
    setNewIngredient({ name: "", unit: "" });
    setMsg("✅ Ingrediente creato");
    loadData();
  }

  if (!rid) return <p className="text-gray-500 text-center py-20">Seleziona un ristorante</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Configurazione</h1>
      <p className="text-sm text-gray-500 mb-8">Mappa prodotti e ingredienti per attivare i suggerimenti automatici sulle forniture.</p>

      {msg && <p className="text-sm bg-green-50 text-green-700 px-3 py-2 rounded-lg mb-4">{msg}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="font-semibold text-gray-800 mb-3">📋 Prodotti</h2>
          <div className="space-y-2 mb-4">
            {products.map(p => (
              <div key={p.id} className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm flex items-center justify-between">
                <span className="text-gray-800">{p.name}</span>
                {p.category && <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{p.category}</span>}
              </div>
            ))}
            {products.length === 0 && <p className="text-xs text-gray-400">Nessun prodotto ancora</p>}
          </div>
          <div className="space-y-2">
            <input value={newProduct.name} onChange={e => setNewProduct(p => ({ ...p, name: e.target.value }))} placeholder="Nome prodotto" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900" />
            <input value={newProduct.category} onChange={e => setNewProduct(p => ({ ...p, category: e.target.value }))} placeholder="Categoria (es. pizza)" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900" />
            <button onClick={createProduct} disabled={!newProduct.name.trim()} className="w-full bg-gray-900 text-white py-2 rounded-lg text-sm hover:bg-gray-700 disabled:opacity-40 transition-colors">+ Aggiungi prodotto</button>
          </div>
        </div>
        <div>
          <h2 className="font-semibold text-gray-800 mb-3">🧂 Ingredienti</h2>
          <div className="space-y-2 mb-4">
            {ingredients.map(i => (
              <div key={i.id} className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm flex items-center justify-between">
                <span className="text-gray-800">{i.name}</span>
                {i.unit && <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{i.unit}</span>}
              </div>
            ))}
            {ingredients.length === 0 && <p className="text-xs text-gray-400">Nessun ingrediente ancora</p>}
          </div>
          <div className="space-y-2">
            <input value={newIngredient.name} onChange={e => setNewIngredient(i => ({ ...i, name: e.target.value }))} placeholder="Nome ingrediente (es. Mozzarella)" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900" />
            <input value={newIngredient.unit} onChange={e => setNewIngredient(i => ({ ...i, unit: e.target.value }))} placeholder="Unità (es. kg, litri)" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900" />
            <button onClick={createIngredient} disabled={!newIngredient.name.trim()} className="w-full bg-gray-900 text-white py-2 rounded-lg text-sm hover:bg-gray-700 disabled:opacity-40 transition-colors">+ Aggiungi ingrediente</button>
          </div>
        </div>
      </div>
    </div>
  );
}
