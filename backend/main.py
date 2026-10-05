"""Campus Customs API.

For now this just reads the catalogue/inventory tables and serves product
images, so the frontend can stop relying on a static JSON snapshot. Problem 5
grows this into the agent backend the chat widget will talk to.
"""

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
IMAGES_DIR = ROOT / "data" / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


class ProductSize(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image: str
    price: float
    sizes: list[ProductSize]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def size_sort_key(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


def row_to_product(conn: sqlite3.Connection, row: sqlite3.Row) -> Product:
    size_rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?",
        (row["product_id"],),
    ).fetchall()
    sizes = sorted(
        (ProductSize(size=r["size"], quantity=r["quantity"]) for r in size_rows),
        key=lambda s: size_sort_key(s.size),
    )
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
        image=f"/images/{Path(row['image_file_path']).name}",
        price=row["price"],
        sizes=sizes,
    )


app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


@app.get("/api/products", response_model=list[Product])
def list_products() -> list[Product]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        return [row_to_product(conn, row) for row in rows]
    finally:
        conn.close()


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return row_to_product(conn, row)
    finally:
        conn.close()
