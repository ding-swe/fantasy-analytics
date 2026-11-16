from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.player_stats import router as player_stats_router
from app.api.routes.free_agents import router as free_agents_router
from app.api.routes.roster import router as roster_router
from app.api.routes.team_comparisons import router as team_comparisons_router

app = FastAPI(
    title="Fantasy Analytics API",
    description="Backend API for NBA fantasy basketball data and analysis.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_stats_router)
app.include_router(roster_router)
app.include_router(free_agents_router)
app.include_router(team_comparisons_router)


@app.get("/", tags=["status"])
def read_root() -> dict[str, str]:
    return {"name": "Fantasy Analytics API", "docs": "/docs"}


@app.get("/health", tags=["status"])
def read_health() -> dict[str, str]:
    return {"status": "ok"}
