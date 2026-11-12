import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from app.schemas import BirthChartRequest
from app.astrology import calculate_chart

app = FastAPI(title="Jyotish Darpan API", version="0.1.0",
              description="Vedic astrology calculation API. Initial release: D1, D9 and Vimshottari Mahadasha.")

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["GET", "POST"], allow_headers=["*"])

@app.get("/")
def root():
    return {"name": "Jyotish Darpan API", "version": "0.1.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Swiss Ephemeris", "ayanamsa": "Lahiri"}

@app.post("/api/v1/chart")
def create_chart(request: BirthChartRequest):
    try:
        return calculate_chart(request.model_dump())
    except Exception as exc:
        # Do not leak internals to public clients; detailed traceback belongs in server logs.
        print(f"Chart calculation failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=422, detail="Chart calculation failed. Check birth time, timezone and coordinates.") from exc
