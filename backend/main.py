# Review Intelligence API v1.0
import sys
import asyncio
from fastapi import FastAPI

# Playwright/Subprocess fix for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import health, analyze, bulk_analyze, summary, history, upload_csv, scrape_analyze
from storage import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Review Intelligence API starting up...")
    yield
    print("Review Intelligence API shutting down...")


app = FastAPI(
    title="Review Intelligence API",
    description="AI-powered customer review analysis system using Groq LLM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(analyze.router, tags=["Analysis"])
app.include_router(bulk_analyze.router, tags=["Bulk Analysis"])
app.include_router(summary.router, tags=["Summary"])
app.include_router(history.router, tags=["History"])
app.include_router(upload_csv.router, tags=["CSV Upload"])
app.include_router(scrape_analyze.router, tags=["Web Scraper"])


@app.get("/")
async def root():
    return {
        "name": "Review Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
