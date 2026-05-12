"""FastAPI wrapper around the claims triage pipeline.

Run with::

    uvicorn api.main:app --reload

The graph is built once at module load — handlers reuse the compiled instance.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from claims_triage.graph import triage
from claims_triage.logging_config import configure_logging
from claims_triage.state import TriageState

configure_logging()


class TriageRequest(BaseModel):
    raw_fnol: str


app = FastAPI(title="Claims Triage")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageState)
def run_triage(request: TriageRequest) -> TriageState:
    return triage(request.raw_fnol)
