"""CRUD for products, ingredients, and product-ingredient mappings."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.db.models import Product, Ingredient, ProductIngredient


# ── Products ──────────────────────────────────────────────────────────────────

def create_product(db: Session, restaurant_id: uuid.UUID, name: str, category: str | None = None) -> Product:
    product = Product(id=uuid.uuid4(), restaurant_id=restaurant_id, name=name.strip(), category=category)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session, restaurant_id: uuid.UUID) -> list[Product]:
    return db.query(Product).filter(Product.restaurant_id == restaurant_id).order_by(Product.name).all()


def get_product(db: Session, product_id: uuid.UUID, restaurant_id: uuid.UUID) -> Product | None:
    return (
        db.query(Product)
        .filter(Product.id == product_id, Product.restaurant_id == restaurant_id)
        .first()
    )


# ── Ingredients ───────────────────────────────────────────────────────────────

def create_ingredient(db: Session, restaurant_id: uuid.UUID, name: str, unit: str | None = None) -> Ingredient:
    ing = Ingredient(id=uuid.uuid4(), restaurant_id=restaurant_id, name=name.strip(), unit=unit)
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return ing


def list_ingredients(db: Session, restaurant_id: uuid.UUID) -> list[Ingredient]:
    return db.query(Ingredient).filter(Ingredient.restaurant_id == restaurant_id).order_by(Ingredient.name).all()


# ── Product ↔ Ingredient mapping ──────────────────────────────────────────────

def set_product_ingredients(
    db: Session, product_id: uuid.UUID, mappings: list[dict[str, Any]]
) -> list[ProductIngredient]:
    """
    Replace all ingredient mappings for a product.
    mappings = [{"ingredient_id": UUID, "quantity_per_unit": float}, ...]
    """
    db.query(ProductIngredient).filter(ProductIngredient.product_id == product_id).delete()
    result = []
    for m in mappings:
        pi = ProductIngredient(
            id=uuid.uuid4(),
            product_id=product_id,
            ingredient_id=m["ingredient_id"],
            quantity_per_unit=m["quantity_per_unit"],
        )
        db.add(pi)
        result.append(pi)
    db.commit()
    return result


def get_product_ingredients(db: Session, product_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = db.query(ProductIngredient).filter(ProductIngredient.product_id == product_id).all()
    return [
        {
            "ingredient_id": str(r.ingredient_id),
            "quantity_per_unit": r.quantity_per_unit,
        }
        for r in rows
    ]


def get_all_product_ingredient_mappings(
    db: Session, restaurant_id: uuid.UUID
) -> dict[str, list[dict[str, Any]]]:
    """
    Returns {product_name: [{ingredient_id, ingredient_name, unit, qty_per_unit}, ...]}
    """
    products = list_products(db, restaurant_id)
    result: dict[str, list[dict[str, Any]]] = {}
    for p in products:
        rows = (
            db.query(ProductIngredient, Ingredient)
            .join(Ingredient, ProductIngredient.ingredient_id == Ingredient.id)
            .filter(ProductIngredient.product_id == p.id)
            .all()
        )
        result[p.name] = [
            {
                "ingredient_id": str(pi.ingredient_id),
                "ingredient_name": ing.name,
                "unit": ing.unit,
                "quantity_per_unit": pi.quantity_per_unit,
            }
            for pi, ing in rows
        ]
    return result
