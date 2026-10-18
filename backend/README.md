# Backend – AI Smart Shopping Assistant (Flask)

Flask REST API + SQLAlchemy/SQLite + Google Gemini (`google-genai` SDK).

```
backend/
├── app.py                      app factory, CORS, error handlers, /api/health
├── config.py                   environment-driven configuration
├── extensions.py               db + cors instances
├── models.py                   Product, ProductPrice, Review, Cart, CartItem, Wishlist, WishlistItem
├── api_utils.py                validation helpers + consistent error format
├── seed.py                     idempotent DEMO data seeding
├── routes/                     products, recommendations, comparisons, reviews, cart, wishlist, chat
├── services/
│   ├── gemini_service.py       all Gemini calls + output validation
│   ├── recommendation_service.py  query parsing, scoring, rule-based fallback
│   └── price_service.py        price-provider interface (add real retailer APIs here)
└── tests/                      pytest suite (in-memory SQLite, Gemini mocked)
```

## Quick start (Windows PowerShell)

```powershell
cd backend
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # then edit GEMINI_API_KEY
python seed.py
python app.py                 # http://127.0.0.1:5000
pytest -q
```

Command Prompt: activate with `venv\Scripts\activate.bat` and copy with `copy .env.example .env`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | _(empty)_ | Gemini key. Backend only; never returned by any endpoint. Without it the app uses rule-based fallbacks. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model name (change if your account uses another). |
| `GEMINI_TIMEOUT_SECONDS` | `20` | Per-request timeout. |
| `DATABASE_URL` | `backend/shop.db` (absolute path built automatically) | Optional SQLAlchemy URL; use an absolute path for SQLite. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed frontend origins. |
| `SECRET_KEY` | dev value | Flask secret. |
| `LOG_LEVEL` | `INFO` | Logging level. |

## Conventions

* **Demo user:** there is no authentication. All cart/wishlist data belongs to a single
  fixed demo user (`demo-user`). Do not deploy this as-is for multiple real users.
* **Errors** always look like `{"error": {"code": "...", "message": "...", "details": {...}}}`
  with codes such as `validation_error` (400), `not_found` (404), `unsupported_media_type` (415),
  `payload_too_large` (413), `out_of_stock`/`no_price` (409), `internal_error` (500).
* **AI-backed responses** include `source` (`"gemini"` or `"rules"`), `ai_generated` (bool) and,
  when a fallback was used, `fallback_reason` (`"ai_not_configured"` or `"ai_error"`).
  A fallback is never labelled as Gemini.
* **Data labelling:** seeded products/prices/ratings/reviews carry `is_sample: true`. Prices are
  never verified unless a real provider stores them with `is_verified = true`.
* JSON request bodies are limited to 64 KB (`MAX_CONTENT_LENGTH`).

## API reference

All paths are prefixed with `/api`.

### `GET /health`
`200` → `{"status":"ok","database":"ok","products":15,"gemini_configured":false,"data_notice":"..."}`
(`gemini_configured` is only a boolean.)

### `GET /products`
Query: `q` (≤200 chars, natural language allowed), `category`, `brand`, `min_price`, `max_price`,
`min_rating` (0–5), `in_stock=true`, `sort` (`relevance|price_asc|price_desc|rating|name`),
`page` (≥1), `per_page` (1–50, default 12). Explicit filters override values parsed from `q`.

`200` →
```json
{"items":[{"id":1,"sku":"SM-001","name":"Nova X1 5G","brand":"Novatech","category":"Smartphones",
  "image_url":"","rating":4.3,"rating_count":1840,"in_stock":true,"stock_note":"...",
  "price":19999.0,"currency":"INR","price_source":"Demo Store A","price_verified":false,
  "is_sample":true,"data_label":"Demo/sample data","source_url":null}],
 "total":1,"page":1,"per_page":12,
 "interpreted_query":{"max_price":3000,"categories":["Headphones"],"keywords":[]},
 "data_notice":"..."}
```
`400` on invalid parameters.

### `GET /products/<id>`
`200` → everything above plus `description`, `specs`, `features`, `data_source`, `prices[]`
(`amount, currency, source, source_url, is_verified, is_sample, label, retrieved_at`),
`review_count`, and `price_comparison` (`prices, cheapest, max_difference, has_verified_prices, note`).
`404` if unknown.

### `GET /categories`
`200` → `{"categories":[{"name":"Laptops","count":3}],"brands":["Aether", ...]}`

### `POST /recommendations`
Body: `{"query": "laptop for programming under ₹60,000", "limit": 5}` (`query` 1–500 chars, `limit` 1–10).
`200` →
```json
{"source":"rules","ai_generated":false,"fallback_reason":"ai_not_configured",
 "parsed":{"max_price":60000,"min_price":null,"categories":["Laptops"],"keywords":["laptop","programming"]},
 "items":[{"product_id":4,"product":{...},"reasons":["..."],"strengths":["..."],
           "limitations":["..."],"budget_fit":"within budget (₹54,990 ≤ ₹60,000)"}],
 "notice":"..."}
```
With Gemini, only product IDs from the retrieved candidates are accepted (unknown IDs are discarded),
facts come from the database, and text quoting prices that are not in the data is removed.
`budget_fit` is always computed from stored prices.

### `POST /compare`
Body: `{"product_ids":[1,2,3]}` (2–4 distinct IDs). `200` →
`{"products":[detail...],"rows":[{"label":"Price","values":[...],"differs":true}],
"highlights":{"cheapest":1,"highest_rated":2,"best_value":1},"price_comparisons":{"1":{...}},
"summary":{"text":"...","key_differences":[],"value_for_money":[],"best_value":null},
"source":"rules","ai_generated":false,"fallback_reason":"...","notice":"..."}`
`404` if a product does not exist.

### `POST /reviews/analyze`
Body (one of): `{"product_id":1}`, `{"reviews":["...","..."]}` (≤50 items), or `{"text":"..."}` (≤8000 chars, split on newlines).
`200` → `{"summary","positives":[],"negatives":[],"common_complaints":[],"reviews_analyzed":3,
"reliable":false,"reliability_note":"Only 3 review(s) ... too small ...","origin":"database",
"is_sample_data":true,"source":"rules","ai_generated":false,"fallback_reason":"..."}`
Fewer than 5 reviews → `reliable: false`.

### Cart (`/cart`)
* `GET /cart` → `{"items":[{"id","product_id","product","quantity","unit_price","line_total","price_is_sample"}],"item_count","total","currency","notice","user"}`
* `POST /cart/items` body `{"product_id":1,"quantity":2}` (quantity 1–10) → `201` + cart. Re-adding merges quantities (max 10 per product). `409` for out-of-stock/unpriced products.
* `PATCH /cart/items/<item_id>` body `{"quantity":3}` → `200` + cart.
* `DELETE /cart/items/<item_id>` → `200` + cart.

Prices and totals are always computed on the server; any price/total sent by a client is ignored.
Payments are not implemented.

### Wishlist (`/wishlist`)
* `GET /wishlist` → `{"items":[{"id","product_id","product","added_at"}],"count","user"}`
* `POST /wishlist/items` body `{"product_id":1}` → `201` (new) or `200` (already present) + wishlist.
* `DELETE /wishlist/items/<item_id>` → `200` + wishlist; `404` if unknown.

### `POST /chat`
Body: `{"message":"Which headphones are best under 3000?","history":[{"role":"user","content":"..."}]}`
(`message` ≤1000 chars; `history` ≤30 items, last 6 used).
`200` → `{"reply":"...","source":"gemini|rules","ai_generated":true,"fallback_reason":null,"product_ids":[7,8]}`.
Relevant product records are retrieved and supplied as context. A Gemini reply that quotes a
rupee amount not present in that context is rejected and replaced by the labelled fallback reply.

## Adding a real retailer price API

1. In `services/price_service.py` subclass `PriceProvider`, set `name`/`is_live = True` and implement
   `fetch_prices(product)` returning dicts with `amount, currency, source, source_url, is_verified,
   is_sample, retrieved_at` – only data actually returned by the retailer's official API
   (respect its terms; do not scrape sites that forbid it).
2. Persist results as `ProductPrice(is_verified=True, is_sample=False, source=..., retrieved_at=...)`
   (e.g. from a scheduled job), or have your provider return them live.
3. Append an instance to `PROVIDERS`. `get_price_comparison` and the UI then show the source and
   last-updated time automatically and stop displaying the "sample only" note.

## Tests

`pytest -q` runs the suite in `tests/` (in-memory SQLite, Gemini calls mocked). It covers product
search/filter/sort, natural-language budgets, cart totals and validation, wishlist persistence,
comparison, review analysis, recommendation validation, price-claim guards, request limits and
the AI fallback paths.
