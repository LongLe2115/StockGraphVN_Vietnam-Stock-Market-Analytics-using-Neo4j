from neo4j_connection import get_neo4j_database, get_neo4j_driver


QUERIES = {
    "q1_stocks_in_banking_sector": """
        MATCH (s:Stock)-[:BELONGS_TO]->(:Sector {name: 'Banking'})
        RETURN s.ticker AS ticker
        ORDER BY ticker
    """,
    "q2_stocks_traded_on_specific_day": """
        MATCH (s:Stock)-[t:TRADED_ON]->(d:TradingDay {date: $date})
        RETURN s.ticker AS ticker, t.close_price AS close_price, t.volume AS volume
        ORDER BY t.volume DESC
    """,
    "q3_sector_stock_count": """
        MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)
        RETURN sec.name AS sector, count(DISTINCT s) AS stock_count
        ORDER BY stock_count DESC, sector
    """,
    "q4_highest_volume_stocks": """
        MATCH (s:Stock)-[t:TRADED_ON]->(d:TradingDay)
        RETURN d.date AS trade_date, s.ticker AS ticker, t.volume AS volume
        ORDER BY t.volume DESC
        LIMIT 10
    """,
    "q5_same_sector_as_fpt": """
        MATCH (:Stock {ticker: 'FPT'})-[:BELONGS_TO]->(sec:Sector)<-[:BELONGS_TO]-(other:Stock)
        RETURN sec.name AS sector, other.ticker AS ticker
        ORDER BY ticker
    """,
    "q6_daily_avg_close_by_sector": """
        MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)
        MATCH (s)-[t:TRADED_ON]->(d:TradingDay)
        RETURN d.date AS trade_date, sec.name AS sector, round(avg(t.close_price), 2) AS avg_close
        ORDER BY trade_date DESC, sector
        LIMIT 30
    """,
    "q7_top_gainers_between_two_days": """
        MATCH (s:Stock)-[t1:TRADED_ON]->(:TradingDay {date: $start_date})
        MATCH (s)-[t2:TRADED_ON]->(:TradingDay {date: $end_date})
        WHERE t1.close_price > 0
        RETURN s.ticker AS ticker,
               round(((t2.close_price - t1.close_price) / t1.close_price) * 100, 2) AS pct_change
        ORDER BY pct_change DESC
    """,
    "q8_most_active_trading_days": """
        MATCH (:Stock)-[t:TRADED_ON]->(d:TradingDay)
        RETURN d.date AS trade_date, sum(t.volume) AS total_volume
        ORDER BY total_volume DESC
        LIMIT 10
    """,
    "q9_company_stock_mapping": """
        MATCH (c:Company)-[:ISSUES]->(s:Stock)-[:BELONGS_TO]->(sec:Sector)
        RETURN c.name AS company, s.ticker AS ticker, sec.name AS sector
        ORDER BY ticker
    """,
    "q10_sector_peers_for_each_stock": """
        MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)<-[:BELONGS_TO]-(peer:Stock)
        WHERE s.ticker <> peer.ticker
        RETURN s.ticker AS ticker, sec.name AS sector, collect(peer.ticker) AS peers
        ORDER BY ticker
    """,
    "q11_stocks_without_trade_on_day": """
        MATCH (s:Stock)
        WHERE NOT (s)-[:TRADED_ON]->(:TradingDay {date: $date})
        RETURN s.ticker AS ticker
        ORDER BY ticker
    """,
}


def run_query(name: str, query: str, **params) -> None:
    print(f"\n===== {name} =====")
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    session_kwargs = {"database": database} if database else {}

    with driver.session(**session_kwargs) as session:
        records = session.run(query, **params).data()
        for row in records[:10]:
            print(row)
        print(f"[INFO] Rows returned: {len(records)}")
    driver.close()


def main() -> None:
    run_query("q1_stocks_in_banking_sector", QUERIES["q1_stocks_in_banking_sector"])
    run_query("q2_stocks_traded_on_specific_day", QUERIES["q2_stocks_traded_on_specific_day"], date="2025-01-10")
    run_query("q3_sector_stock_count", QUERIES["q3_sector_stock_count"])
    run_query("q4_highest_volume_stocks", QUERIES["q4_highest_volume_stocks"])
    run_query("q5_same_sector_as_fpt", QUERIES["q5_same_sector_as_fpt"])
    run_query("q6_daily_avg_close_by_sector", QUERIES["q6_daily_avg_close_by_sector"])
    run_query(
        "q7_top_gainers_between_two_days",
        QUERIES["q7_top_gainers_between_two_days"],
        start_date="2025-01-02",
        end_date="2025-01-10",
    )
    run_query("q8_most_active_trading_days", QUERIES["q8_most_active_trading_days"])
    run_query("q9_company_stock_mapping", QUERIES["q9_company_stock_mapping"])
    run_query("q10_sector_peers_for_each_stock", QUERIES["q10_sector_peers_for_each_stock"])
    run_query("q11_stocks_without_trade_on_day", QUERIES["q11_stocks_without_trade_on_day"], date="2025-01-10")


if __name__ == "__main__":
    main()
