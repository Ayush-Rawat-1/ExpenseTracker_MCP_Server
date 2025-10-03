from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

app = FastAPI(title="Expense Tracker API")

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
    except sqlite3.Error as e:
        raise RuntimeError(f"Database init failed: {e}")

init_db()

class Expense(BaseModel):
    date: str
    amount: float
    category: str
    subcategory: str = ""
    note: str = ""

@app.post("/expenses")
def add_expense(expense: Expense):
    try:
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (expense.date, expense.amount, expense.category, expense.subcategory, expense.note)
            )
            return {"status": "ok", "id": cur.lastrowid}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/expenses")
def list_expenses(start_date: str = Query(...), end_date: str = Query(...)):
    try:
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/expenses/summary")
def summarize(start_date: str, end_date: str, category: str | None = None):
    try:
        with sqlite3.connect(DB_PATH) as c:
            query = """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            cur = c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
