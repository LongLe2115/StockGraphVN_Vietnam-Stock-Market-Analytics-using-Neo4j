# Vietnam Stock Analytics with Neo4j (MVP)

Phase 1 goal: validate that Neo4j is a good fit for stock market relationship modeling using a small local pipeline.

## 1) Recommended Folder Structure

```text
project/
  data/
    raw/
    processed/
  src/
    crawler/
      fetch_stock_data.py
    etl/
      clean_stock_data.py
    neo4j/
      neo4j_connection.py
      load_to_neo4j.py
      run_queries.py
  notebooks/
  tests/
  requirements.txt
  .env.example
  README.md
```

## 2) Python Modules Included

- `fetch_stock_data.py`: pulls OHLCV data for 10 VN tickers and saves raw CSV.
- `clean_stock_data.py`: validates schema, converts types, removes bad rows, saves processed CSV.
- `neo4j_connection.py`: creates Neo4j driver from `.env`.
- `load_to_neo4j.py`: creates constraints and loads nodes + relationships.
- `run_queries.py`: executes practical Cypher queries for validation.

## 3) Requirements

Install from:

```bash
pip install -r requirements.txt
```

## 4) .env Example

Copy and rename:

```bash
cp .env.example .env
```

Then edit:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

## 5) Step-by-Step Execution Order (Zero to Running)

1. Install Python 3.10+.
2. Start Neo4j locally (Desktop or Community), create DB, note credentials.
3. Create virtual environment and install dependencies:
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
     - `pip install -r requirements.txt`
4. Create `.env` from `.env.example`, fill Neo4j credentials.
5. Fetch raw data:
   - `python src/crawler/fetch_stock_data.py`
6. Clean and transform:
   - `python src/etl/clean_stock_data.py`
7. Load into Neo4j:
   - `python src/neo4j/load_to_neo4j.py`
8. Run graph queries:
   - `python src/neo4j/run_queries.py`
9. Open Neo4j Browser and run any query manually to inspect graph.

## 6) Cypher Query Set (11 Queries)

### Q1. Find all stocks in Banking sector
```cypher
MATCH (s:Stock)-[:BELONGS_TO]->(:Sector {name: 'Banking'})
RETURN s.ticker AS ticker
ORDER BY ticker;
```

### Q2. Find stocks traded on a specific day
```cypher
MATCH (s:Stock)-[t:TRADED_ON]->(d:TradingDay {date: '2025-01-10'})
RETURN s.ticker AS ticker, t.close_price AS close_price, t.volume AS volume
ORDER BY t.volume DESC;
```

### Q3. Compare sectors by stock count
```cypher
MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)
RETURN sec.name AS sector, count(DISTINCT s) AS stock_count
ORDER BY stock_count DESC, sector;
```

### Q4. Highest volume stock-day records
```cypher
MATCH (s:Stock)-[t:TRADED_ON]->(d:TradingDay)
RETURN d.date AS trade_date, s.ticker AS ticker, t.volume AS volume
ORDER BY t.volume DESC
LIMIT 10;
```

### Q5. Stocks in same sector as FPT
```cypher
MATCH (:Stock {ticker: 'FPT'})-[:BELONGS_TO]->(sec:Sector)<-[:BELONGS_TO]-(other:Stock)
RETURN sec.name AS sector, other.ticker AS ticker
ORDER BY ticker;
```

### Q6. Daily average close price by sector
```cypher
MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)
MATCH (s)-[t:TRADED_ON]->(d:TradingDay)
RETURN d.date AS trade_date, sec.name AS sector, round(avg(t.close_price), 2) AS avg_close
ORDER BY trade_date DESC, sector;
```

### Q7. Top gainers between two days
```cypher
MATCH (s:Stock)-[t1:TRADED_ON]->(:TradingDay {date: '2025-01-02'})
MATCH (s)-[t2:TRADED_ON]->(:TradingDay {date: '2025-01-10'})
WHERE t1.close_price > 0
RETURN s.ticker AS ticker,
       round(((t2.close_price - t1.close_price) / t1.close_price) * 100, 2) AS pct_change
ORDER BY pct_change DESC;
```

### Q8. Most active trading days by total volume
```cypher
MATCH (:Stock)-[t:TRADED_ON]->(d:TradingDay)
RETURN d.date AS trade_date, sum(t.volume) AS total_volume
ORDER BY total_volume DESC
LIMIT 10;
```

### Q9. Company -> Stock -> Sector mapping
```cypher
MATCH (c:Company)-[:ISSUES]->(s:Stock)-[:BELONGS_TO]->(sec:Sector)
RETURN c.name AS company, s.ticker AS ticker, sec.name AS sector
ORDER BY ticker;
```

### Q10. Sector peers for each stock
```cypher
MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)<-[:BELONGS_TO]-(peer:Stock)
WHERE s.ticker <> peer.ticker
RETURN s.ticker AS ticker, sec.name AS sector, collect(peer.ticker) AS peers
ORDER BY ticker;
```

### Q11. Stocks without trade record on a day
```cypher
MATCH (s:Stock)
WHERE NOT (s)-[:TRADED_ON]->(:TradingDay {date: '2025-01-10'})
RETURN s.ticker AS ticker
ORDER BY ticker;
```

## 7) Why Neo4j Is Better Than SQL Here (Practical MVP View)

1. Relationship-first questions are simpler:
   - Neo4j: `(:Stock)-[:BELONGS_TO]->(:Sector)` traversal is direct.
   - SQL: multiple joins across stock, sector, company, daily tables.

2. Natural multi-hop analytics:
   - Example: "Find peers of FPT in same sector and compare their trading behavior over date range."
   - In Neo4j, this is an intuitive graph pattern match; in SQL it quickly becomes complex nested joins.

3. Flexible model evolution:
   - You can add new nodes like `:News`, `:Investor`, `:Broker` and relationships without heavy schema migrations.
   - Useful when your stock analytics ideas change every week in early project phase.

4. Better readability for business logic:
   - Cypher expresses domain logic close to business language (company issues stock, stock belongs to sector, stock traded on day).
   - Easier for quick experimentation during MVP.

5. Fast validation for connected insights:
   - Your Phase 1 goal is not BI dashboards; it is relationship validation.
   - Graph queries give immediate evidence for connected patterns with less query friction.

## MVP Scope Guardrails

- Keep only the 10 target tickers.
- Keep local files + local Neo4j only.
- No dashboards, no ML, no cloud deployment.
- Focus on clean ETL, graph import, and query validation.
