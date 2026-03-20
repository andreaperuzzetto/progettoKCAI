"""Products and ingredients CRUD endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant
from backend.services.products_service import (
    create_product, list_products, get_product,
    create_ingredient, list_ingredients,
    set_product_ingredients, get_product_ingredients,
)

router = APIRouter(tags=["products"])


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    category: Optional[str] = None


@router.post("/products")
def api_create_product(
    body: ProductCreate,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    p = create_product(db, restaurant.id, body.name, body.category)
    return {"id": str(p.id), "name": p.name, "category": p.category}


@router.get("/products")
def api_list_products(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    products = list_products(db, restaurant.id)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category,
            "ingredients": get_product_ingredients(db, p.id),
        }
        for p in products
    ]


# ── Ingredients ───────────────────────────────────────────────────────────────

class IngredientCreate(BaseModel):
    name: str
    unit: Optional[str] = None


@router.post("/ingredients")
def api_create_ingredient(
    body: IngredientCreate,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    ing = create_ingredient(db, restaurant.id, body.name, body.unit)
    return {"id": str(ing.id), "name": ing.name, "unit": ing.unit}


@router.get("/ingredients")
def api_list_ingredients(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    ings = list_ingredients(db, restaurant.id)
    return [{"id": str(i.id), "name": i.name, "unit": i.unit} for i in ings]


# ── Product ↔ Ingredient mapping ──────────────────────────────────────────────

class IngredientMapping(BaseModel):
    ingredient_id: uuid.UUID
    quantity_per_unit: float


@router.post("/products/{product_id}/ingredients")
def api_set_product_ingredients(
    product_id: uuid.UUID,
    mappings: list[IngredientMapping],
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    p = get_product(db, product_id, restaurant.id)
    if not p:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    set_product_ingredients(db, product_id, [m.model_dump() for m in mappings])
    return {"product_id": str(product_id), "mappings_set": len(mappings)}
