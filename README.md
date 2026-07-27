# RecipeBox

Find and generate recipes you can make using only the ingredients you already have.

Hybrid flow:

1. Look up recipes from **TheMealDB** (free)
2. Validate every recipe against your ingredients + pantry (server-side)
3. Optionally **generate** recipes with **Google Gemini** (free AI Studio key) — falls back to templates if no key
4. Reject any recipe (API or generated) that needs surprise ingredients

## Stack (all free)

- **Frontend:** Next.js (App Router) + TypeScript
- **Backend:** FastAPI + Uvicorn
- **Recipe API:** [TheMealDB](https://www.themealdb.com/api.php) free endpoints
- **Generation:** [Google AI Studio / Gemini](https://aistudio.google.com/apikey) (`gemini-2.0-flash`) + template fallback
- **Persistence:** Supabase (auth + pantry + favourites) with `localStorage` fallback for guests
- **Auth DB:** [Supabase](https://supabase.com) free tier

## Quick start (local)

### 1. Environment

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

### 2. Supabase (login + database)

1. Create a free project at https://supabase.com
2. Copy **Project URL** and **anon public** key into `frontend/.env.local`:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. In Supabase → **SQL Editor**, run the contents of [`supabase/schema.sql`](supabase/schema.sql)
4. (Optional) Authentication → Providers → Email: disable “Confirm email” for faster local testing

Without these keys the app still works for guests; Sign in syncs pantry/favourites.

### 2b. Google Gemini (better recipe generation — free)

1. Create a free API key at https://aistudio.google.com/apikey  
2. Add to project `.env`:

```env
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

3. Restart the backend

Without `GOOGLE_API_KEY`, generate still works using a simple template fallback (lower quality).

### 3. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/api/health

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:3000 — use **Sign in** to create an account and sync pantry/favourites.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health check |
| GET | `/api/pantry/defaults` | Basic + optional pantry lists |
| POST | `/api/ingredients/normalize` | Normalise ingredient strings |
| POST | `/api/recipes/search` | Search + exact/near match grouping |
| POST | `/api/recipes/generate` | Free generated recipe (allowed ingredients only) |
| POST | `/api/recipes/validate` | Re-validate a recipe against allowed ingredients |

### Search body example

```json
{
  "ingredients": ["chicken breast", "rice", "tomatoes", "onion"],
  "pantry_defaults": ["salt", "black pepper", "cooking oil", "paprika"],
  "diet": null,
  "exclude_ingredients": [],
  "maximum_missing_ingredients": 2,
  "include_ai_if_sparse": false
}
```

## Matching rule

The backend never trusts the recipe API or generator alone:

```text
allowed = user_ingredients + pantry_defaults
required = recipe_ingredients - pantry_defaults
missing = required - allowed

exact  → missing == 0
near   → missing ≤ maximum (default 2)
reject → otherwise
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## MVP notes

- Guests use `localStorage`; signed-in users sync pantry + favourites via Supabase
- Quantity-aware matching is out of scope for v1
- Generated recipes are template-based (free); swap in another free model later if desired
- TheMealDB free API filters by one ingredient; RecipeBox merges queries and validates itself
