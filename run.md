# Run Guide (Windows + PowerShell)

File này hướng dẫn chạy toàn bộ project từ đầu đến cuối trên máy local.

## 1) Chuẩn bị

- Cài Python 3.10+.
- Cài và chạy Neo4j Desktop (hoặc Neo4j Community local).
- Tạo database Neo4j, nhớ `username/password`.

## 2) Mở project

Trong PowerShell:

```powershell
cd "d:\project neo4j"
```

## 3) Tạo môi trường ảo và cài thư viện

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 4) Cấu hình Neo4j credentials

Tạo file `.env` từ mẫu:

```powershell
Copy-Item ".env.example" ".env"
```

Mở `.env` và cập nhật:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

## 5) Chạy pipeline dữ liệu

### Bước 1: Crawl dữ liệu Vietstock

```powershell
python src/crawler/fetch_stock_data.py
```

Kết quả tạo file:
- `data/raw/vn_stock_prices_raw.csv`

### Bước 2: Clean + transform

```powershell
python src/etl/clean_stock_data.py
```

Kết quả tạo file:
- `data/processed/vn_stock_prices_processed.csv`

### Bước 3: Load vào Neo4j

```powershell
python src/neo4j/load_to_neo4j.py
```

Script sẽ:
- tạo constraints
- tạo nodes/relationships
- upsert dữ liệu giao dịch

### Bước 4: Chạy query kiểm tra

```powershell
python src/neo4j/run_queries.py
```

## 6) Chạy nhanh toàn bộ (sau khi đã setup xong)

```powershell
python src/crawler/fetch_stock_data.py; `
python src/etl/clean_stock_data.py; `
python src/neo4j/load_to_neo4j.py; `
python src/neo4j/run_queries.py
```

## 7) Kiểm tra trong Neo4j Browser (optional)

Mở Neo4j Browser và chạy:

```cypher
MATCH (n) RETURN labels(n) AS labels, count(*) AS cnt;
```

```cypher
MATCH (s:Stock)-[r:TRADED_ON]->(d:TradingDay)
RETURN s.ticker, d.date, r.close_price, r.volume
ORDER BY d.date DESC
LIMIT 20;
```

## 8) Lỗi thường gặp

- `Missing Neo4j credentials`:
  - chưa tạo `.env` hoặc điền thiếu biến.
- `Connection refused`:
  - Neo4j chưa chạy hoặc sai port (`7687`).
- Crawl fail:
  - kiểm tra mạng, chạy lại sau vài phút (website có thể throttle tạm thời).

## 9) Gợi ý workflow hằng ngày

```powershell
.venv\Scripts\Activate.ps1
python src/crawler/fetch_stock_data.py
python src/etl/clean_stock_data.py
python src/neo4j/load_to_neo4j.py
python src/neo4j/run_queries.py
```

