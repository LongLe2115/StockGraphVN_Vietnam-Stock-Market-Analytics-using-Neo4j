from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


TICKERS = ["FPT", "HPG", "VIC", "VHM", "VCB", "BID", "MWG", "MSN", "SSI", "VNM"]

# Lightweight metadata for MVP.
STOCK_METADATA = {
    "FPT": {"company_name": "FPT Corporation", "sector": "Technology", "exchange": "HOSE"},
    "HPG": {"company_name": "Hoa Phat Group", "sector": "Materials", "exchange": "HOSE"},
    "VIC": {"company_name": "Vingroup JSC", "sector": "Real Estate", "exchange": "HOSE"},
    "VHM": {"company_name": "Vinhomes JSC", "sector": "Real Estate", "exchange": "HOSE"},
    "VCB": {"company_name": "Vietcombank", "sector": "Banking", "exchange": "HOSE"},
    "BID": {"company_name": "BIDV", "sector": "Banking", "exchange": "HOSE"},
    "MWG": {"company_name": "Mobile World Group", "sector": "Retail", "exchange": "HOSE"},
    "MSN": {"company_name": "Masan Group", "sector": "Consumer", "exchange": "HOSE"},
    "SSI": {"company_name": "SSI Securities", "sector": "Financial Services", "exchange": "HOSE"},
    "VNM": {"company_name": "Vinamilk", "sector": "Consumer", "exchange": "HOSE"},
}

BASE_URL = "https://finance.vietstock.vn"
DETAIL_URL = "https://finance.vietstock.vn/data/getstockdealdetailbytime"


@dataclass
class FetchConfig:
    days_back: int = 90
    time_type: str = "3M"
    timeout_seconds: int = 30


def _parse_ms_date(raw: str) -> str | None:
    # Example: "/Date(1776877200000)/"
    if not raw:
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return None
    ts_ms = int(digits)
    return datetime.fromtimestamp(ts_ms / 1000, UTC).strftime("%Y-%m-%d")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _map_price_record(record: dict[str, Any], ticker: str) -> dict[str, Any] | None:
    """Map Vietstock deal-detail payload to canonical schema."""
    trade_date = _parse_ms_date(record.get("TradingDate"))
    close_price = _to_float(record.get("Price"))
    volume = _to_int(record.get("Vol"))

    if not trade_date or close_price is None or volume is None:
        return None

    return {
        "ticker": ticker,
        "company_name": STOCK_METADATA[ticker]["company_name"],
        "sector": STOCK_METADATA[ticker]["sector"],
        "exchange": STOCK_METADATA[ticker]["exchange"],
        "trade_date": trade_date,
        # Endpoint currently provides close + volume only; keep MVP pipeline simple.
        "open_price": close_price,
        "high_price": close_price,
        "low_price": close_price,
        "close_price": close_price,
        "volume": volume,
    }


def fetch_ticker_data(session: requests.Session, ticker: str, config: FetchConfig) -> list[dict[str, Any]]:
    referer = f"{BASE_URL}/{ticker}/thong-ke-giao-dich.htm"
    page_response = session.get(referer, timeout=config.timeout_seconds)
    page_response.raise_for_status()

    token_marker = 'name=__RequestVerificationToken type=hidden value='
    html = page_response.text
    token_index = html.find(token_marker)
    if token_index < 0:
        raise ValueError(f"Could not find verification token for {ticker}")
    token_start = token_index + len(token_marker)
    token_end = html.find(">", token_start)
    token = html[token_start:token_end].strip().strip('"')

    headers = {
        "Origin": BASE_URL,
        "Referer": referer,
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {
        "code": ticker,
        "timeType": config.time_type,
        "__RequestVerificationToken": token,
    }
    response = session.post(DETAIL_URL, data=payload, headers=headers, timeout=config.timeout_seconds)
    response.raise_for_status()

    rows = response.json()
    if not isinstance(rows, list):
        return []

    mapped: list[dict[str, Any]] = []
    for row in rows:
        item = _map_price_record(row, ticker)
        if item:
            mapped.append(item)

    mapped.sort(key=lambda x: x["trade_date"])
    # Keep only recent N days based on config.
    return mapped[-config.days_back :]


def main() -> None:
    config = FetchConfig()
    output_path = Path("data/raw/vn_stock_prices_raw.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []
    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        for ticker in TICKERS:
            try:
                ticker_rows = fetch_ticker_data(session, ticker, config)
                print(f"[OK] {ticker}: fetched {len(ticker_rows)} rows")
                all_rows.extend(ticker_rows)
            except (requests.RequestException, ValueError) as exc:
                print(f"[WARN] {ticker}: fetch failed - {exc}")

    if not all_rows:
        raise RuntimeError("No data fetched. Check internet/API availability.")

    df = pd.DataFrame(all_rows)
    df.to_csv(output_path, index=False)
    print(f"[DONE] Raw CSV saved to: {output_path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
