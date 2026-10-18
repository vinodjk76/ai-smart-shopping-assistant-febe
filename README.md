# AI Smart Shopping Assistant

React (Vite) + Flask + SQLite + Google Gemini. Search products (including natural-language queries),
get AI recommendations, compare products, analyze reviews, manage a cart and wishlist, and chat with a
shopping assistant. Everything works without a Gemini key using clearly-labelled rule-based fallbacks.

> **Demo data:** all seeded products, prices, ratings and reviews are fictional **sample data** and are
> labelled as such in the UI. No live retailer API is configured and no payments are processed.
> There is no authentication: cart and wishlist belong to one fixed demo user.

## How the pieces fit together

```
React (Vite, :5173) ──axios──▶ Flask REST API (:5000) ──SQLAlchemy──▶ SQLite (backend/shop.db)
                                     │
                                     └──google-genai──▶ Gemini (key lives only in backend/.env)
```

* **Frontend** – pages for Dashboard, Browse/Search, Product details, Compare, AI Picks, Review analyzer,
  Cart, Wishlist, plus a floating chat widget. Shared state (cart, wishlist, compare list, toasts) is in
  `hooks/useShop.jsx`; all HTTP calls are in `api/client.js` (base URL from `VITE_API_URL`).
* **Backend** – routes validate input and read/write SQLite. For AI features the backend first retrieves
  candidate products from the database, then asks Gemini to rank/explain/summarise **only that data**.
  Returned product IDs are checked against the candidates, product facts and budget fit come from the
  database, and free text that quotes prices not in the data is discarded. If Gemini is not configured,
  fails, times out or returns malformed output, a deterministic algorithm answers instead and the response is
  labelled `source: "rules"`, `ai_generated: false` (never presented as Gemini).
* **Database** – `Product`, `ProductPrice` (source, currency, timestamp, verified flag), `Review`,
  `Cart`/`CartItem`, `Wishlist`/`WishlistItem`, with keys, relationships, indexes, unique/check constraints.
* **Security** – key only in backend env; CORS limited to `CORS_ORIGINS`; 64 KB request limit; input
  length/type validation on both sides; ORM only; cart totals computed server-side; only trimmed product
  data (no personal data) is sent to Gemini.

## Windows setup

### 1. Install prerequisites
* Python 3.11+ from <https://www.python.org/downloads/> (tick **Add python.exe to PATH**).
* Node.js 20+ LTS (includes npm) from <https://nodejs.org/>.
* Verify: `python --version`, `node --version`, `npm --version`.

### 2. Backend
PowerShell:
```powershell
cd ai-smart-shopping-assistant\backend
python -m venv venv
.\venv\Scripts\Activate.ps1        # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
copy .env.example .env
notepad .env                        # set GEMINI_API_KEY=... (optional)
python seed.py                      # creates shop.db and loads sample data (safe to rerun)
python app.py                       # API on http://127.0.0.1:5000
```
Command Prompt equivalents: `venv\Scripts\activate.bat`, same other commands.

Get a Gemini API key at <https://aistudio.google.com/apikey>. Check `http://127.0.0.1:5000/api/health`
(`gemini_configured` should be `true` if the key was picked up; restart the server after editing `.env`).

### 3. Frontend (second terminal)
```powershell
cd ai-smart-shopping-assistant\frontend
npm install
copy .env.example .env              # VITE_API_URL=http://127.0.0.1:5000/api
npm run dev                         # http://127.0.0.1:5173
```
Open <http://127.0.0.1:5173> (use `127.0.0.1` or `localhost` – both are allowed by default CORS settings).

### 4. Try every feature
1. **Dashboard** – featured products, category tiles, budget picks, example searches.
2. **Browse** – search “Find the best headphones under ₹3,000”; the page shows how it understood the query.
   Try filters (price, category, brand, rating) and sorting.
3. **Product page** – specs, sample price table with source/last-updated, “Analyze reviews”, Add to cart,
   Wishlist, Compare, **Ask AI** (opens the chat with a prefilled question).
4. **AI Picks** – “Recommend a laptop for programming under ₹60,000”. Badge shows Gemini vs rule-based.
5. **Compare** – select 2–4 products (cards or dropdown); differing rows are highlighted.
6. **Reviews** – analyze stored reviews or paste your own; note the “too small a sample” warning (<5 reviews).
7. **Cart** – change quantities (1–10), remove items, check totals. **Wishlist** – save/remove, move to cart.
   Reload the page: both persist in SQLite.
8. **Chat** – bottom-right button; try “Compare smartphones with good battery life”; use **Clear chat**.
9. Stop the backend to see friendly error states, then restart it.

### 5. Run backend tests
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -q
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python` not found | Reinstall Python with “Add to PATH”, or use `py -3.11`. |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use Command Prompt. |
| `ModuleNotFoundError` | The venv is not active or `pip install -r requirements.txt` was not run. |
| Frontend shows “Cannot reach the server” | Start the backend; check `VITE_API_URL` in `frontend/.env` (restart `npm run dev` after editing). |
| Browser console shows a CORS error | Add your frontend origin to `CORS_ORIGINS` in `backend/.env` and restart Flask. |
| `gemini_configured: false` | `.env` must be in `backend/`, with `GEMINI_API_KEY=` set and no quotes/spaces; restart Flask. |
| Responses say “Rule-based (not AI)” though a key is set | The Gemini call failed (invalid key, quota/rate limit, model name, network). Check the Flask log (`Gemini call failed: <ErrorType>`) and `GEMINI_MODEL`. |
| Empty product list | Run `python seed.py`. |
| Port 5000/5173 in use | Stop the other process, or change the port in `app.py` / `vite.config.js` (and update `CORS_ORIGINS` / `VITE_API_URL`). |
| Want a clean database | Stop the backend, delete `backend/shop.db`, run `python seed.py`. |

## Adding a real retailer API
See “Adding a real retailer price API” in `backend/README.md`: implement a `PriceProvider` in
`services/price_service.py`, store results as verified `ProductPrice` rows with source and timestamp, and
register the provider. Only use official APIs permitted by the retailer's terms; never fabricate prices,
links or availability.

## Deployment options
* **Frontend** (static): `npm run build`, then host `frontend/dist` on Netlify, Vercel, Cloudflare Pages,
  GitHub Pages or any static host. Set `VITE_API_URL` to the public API URL **at build time**.
* **Backend**: run behind a production WSGI server instead of `python app.py`, e.g. `pip install gunicorn`
  and `gunicorn "app:create_app()"` on Linux (on Windows hosts use `waitress`: `waitress-serve --call app:create_app`).
  Platforms: Render, Railway, Fly.io, Azure App Service, or a VM/container. Set `GEMINI_API_KEY`,
  `SECRET_KEY`, `CORS_ORIGINS` (your frontend URL) as environment variables.
* **Before real use:** SQLite files are fine for a demo but use a managed database (set `DATABASE_URL`) for
  anything multi-instance; add real authentication and per-user carts; add rate limiting; serve over HTTPS.

## Verification status of this delivery
See the notes in the hand-off message: the automated tests (`pytest`) and `npm run build` could **not** be
executed in the environment where this code was generated (package registries were blocked), so please run
them locally using the steps above.
