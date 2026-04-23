from pathlib import Path

import pandas as pd

from neo4j_connection import get_neo4j_database, get_neo4j_driver


PROCESSED_PATH = Path("data/processed/vn_stock_prices_processed.csv")


CREATE_CONSTRAINTS = [
    "CREATE CONSTRAINT stock_ticker IF NOT EXISTS FOR (s:Stock) REQUIRE s.ticker IS UNIQUE",
    "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT sector_name IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT trading_day_date IF NOT EXISTS FOR (d:TradingDay) REQUIRE d.date IS UNIQUE",
]


UPSERT_QUERY = """
UNWIND $rows AS row
MERGE (stock:Stock {ticker: row.ticker})
MERGE (company:Company {name: row.company_name})
MERGE (sector:Sector {name: row.sector})
MERGE (day:TradingDay {date: row.trade_date})

MERGE (company)-[:ISSUES]->(stock)
MERGE (stock)-[:BELONGS_TO]->(sector)

MERGE (stock)-[r:TRADED_ON]->(day)
SET r.open_price = row.open_price,
    r.high_price = row.high_price,
    r.low_price = row.low_price,
    r.close_price = row.close_price,
    r.volume = row.volume,
    r.exchange = row.exchange
"""


def main() -> None:
    if not PROCESSED_PATH.exists():
        raise FileNotFoundError(f"Processed file not found: {PROCESSED_PATH}")

    df = pd.read_csv(PROCESSED_PATH)
    records = df.to_dict("records")
    if not records:
        raise ValueError("No records found in processed CSV.")

    driver = get_neo4j_driver()
    database = get_neo4j_database()
    session_kwargs = {"database": database} if database else {}

    with driver.session(**session_kwargs) as session:
        for query in CREATE_CONSTRAINTS:
            session.run(query)

        # Chunk inserts for basic safety on lower-memory local machines.
        chunk_size = 1000
        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            session.run(UPSERT_QUERY, rows=chunk)

    driver.close()
    print(f"[DONE] Loaded {len(records)} records into Neo4j")


if __name__ == "__main__":
    main()
