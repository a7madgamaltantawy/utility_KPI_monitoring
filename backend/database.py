from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("data/database/utility_kpi.db")

def query_db(sql: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df