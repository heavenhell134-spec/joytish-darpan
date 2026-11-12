# Jyotish Darpan — full-stack starter (v0.1)

A first working foundation for a Vedic astrology platform. This is not yet a complete AstroTalk competitor. It currently provides a real calculation API and a small web UI for:

- Sidereal planetary longitudes using Lahiri ayanamsa
- Ascendant calculation from local birth time, IANA timezone and coordinates
- Whole-sign D1 (Rashi) chart
- D9 (Navamsha) chart
- Nakshatra and pada for each graha
- True Rahu and opposite Ketu
- Retrograde flag based on apparent longitude speed
- Vimshottari Mahadasha sequence and birth balance

## Project layout

- `backend/` — FastAPI calculation API
- `frontend/` — Next.js web interface

## Important licensing decision — read before public deployment

The Python `pyswisseph` binding uses Swiss Ephemeris. Swiss Ephemeris is dual-licensed under AGPL-3.0 or a commercial Professional License. Before distributing the software or activating a public service, choose and comply with one licensing route. The AGPL route can require the complete corresponding source of the network service to be offered under AGPL-compatible terms. If Jyotish Darpan is intended to remain proprietary, obtain the appropriate commercial license from Astrodienst or replace the engine with a separately reviewed permissively licensed alternative. Do not launch a closed-source public service using this dependency without resolving the license.

Official information: https://www.astro.com/swisseph/swephinfo_g.htm

## Run locally

### 1. Backend

Python 3.11+ recommended.

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` to test the API. Health check: `http://localhost:8000/health`.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then:

```bash
npm run dev
```

Open `http://localhost:3000`.

## API request example

`POST /api/v1/chart`

```json
{
  "name": "Example",
  "birth_date": "2000-01-01",
  "birth_time": "12:00:00",
  "timezone": "Asia/Kolkata",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "ayanamsa": "lahiri",
  "house_system": "whole_sign"
}
```

The API requires the actual IANA timezone and latitude/longitude of the birthplace. Do not use an approximate city centre for a final chart when exact birth coordinates are available. Birth time accuracy also matters.

## GitHub + Vercel deployment

Recommended simple deployment: one GitHub repository, two Vercel projects.

1. Push this repository to GitHub.
2. Create Vercel Project A from the repo; set **Root Directory** to `frontend`. Add `NEXT_PUBLIC_API_URL` with the deployed backend URL, e.g. `https://your-api.vercel.app`.
3. Create Vercel Project B from the same repo; set **Root Directory** to `backend`. Vercel supports FastAPI deployments. Set `CORS_ORIGINS` to the exact frontend deployment URL (comma-separated if using preview + production domains).
4. Deploy backend first, test `/health` and `/docs`, then deploy frontend.
5. For a production setup, add a custom domain, configure strict CORS, secrets, logging, monitoring and rate limiting.

Official Vercel FastAPI guide: https://vercel.com/docs/frameworks/backend/fastapi
Official Vercel Git deployment guide: https://vercel.com/docs/git

## What is deliberately not included yet

No user accounts, database persistence, saved charts, place-name geocoding, payment, astrologer marketplace, chat/video, PDF report generation, Shadbala, Ashtakavarga, divisional charts beyond D9, Bhava Chalit, yogas, transit engine or AI interpretations. These should be built in separate tested modules rather than faked in the UI.

## Accuracy and validation checklist before launch

- Validate sample charts against a trusted reference implementation using identical timezone, coordinates, ayanamsa, node type and house conventions.
- Add regression fixtures for different centuries, leap days, DST zones and latitudes near the polar circles.
- Confirm exact convention for true vs mean Rahu; current engine uses **true node**.
- Confirm the D9 mapping and Vimshottari year-length convention with a qualified Vedic astrology reviewer.
- Add tests for house cusps and chart edge cases.
- Obtain legal review of Swiss Ephemeris licensing.

## Database foundation (not wired into the API yet)

`supabase/migrations/0001_initial_schema.sql` creates the initial user profile, birth profile and saved chart tables with row-level security. The current chart endpoint is stateless and does **not** save data yet. Supabase Auth integration and chart persistence are the next backend milestone.
