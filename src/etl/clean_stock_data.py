from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw/vn_stock_prices_raw.csv")
PROCESSED_PATH = Path("data/processed/vn_stock_prices_processed.csv")

REQUIRED_COLUMNS = [
    "ticker",
    "company_name",
    "sector",
    "exchange",
    "trade_date",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
]


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw file not found: {RAW_PATH}")

    df = pd.read_csv(RAW_PATH)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in raw file: {missing_cols}")

    df = df[REQUIRED_COLUMNS].copy()

    for col in ["open_price", "high_price", "low_price", "close_price", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.date

    df = df.dropna(subset=["ticker", "company_name", "sector", "trade_date", "close_price", "volume"])
    df = df[df["volume"] >= 0]
    df = df[df["close_price"] > 0]

    # Keep one row per ticker-day for stable graph imports.
    df = df.sort_values(["ticker", "trade_date"]).drop_duplicates(["ticker", "trade_date"], keep="last")

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)

    print(f"[DONE] Processed CSV saved to: {PROCESSED_PATH}")
    print(f"[INFO] Rows: {len(df)} | Stocks: {df['ticker'].nunique()} | Dates: {df['trade_date'].nunique()}")


if __name__ == "__main__":
    main()
