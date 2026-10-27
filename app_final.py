import os
import sys
import time
from datetime import datetime, timezone
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    stream=sys.stdout,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("support-tickets")

app = FastAPI(
    title="Support Ticket Service",
    description="A small API for creating and tracking support requests.",
    version=APP_VERSION,
)


@app.on_event("startup")
def log_startup() -> None:
    logger.info(
        "Support ticket service started (version=%s, log_level=%s)",
        APP_VERSION,
        LOG_LEVEL,
    )


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


tickets: dict = {}
_next_id = 1

STATUSES = ["open", "in_progress", "closed"]


class TicketCreate(BaseModel):
    name: str = Field(..., min_length=1, examples=["Alice"])
    email: str = Field(..., examples=["alice@example.com"])
    message: str = Field(..., min_length=1, examples=["Cannot log in"])


class ReplyCreate(BaseModel):
    message: str = Field(..., min_length=1, examples=["We are looking into it"])
    status: Optional[str] = Field("in_progress", examples=["in_progress", "closed"])


class Ticket(TicketCreate):
    id: int
    status: str
    created_at: str
    updated_at: str
    replies: List[dict]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_ticket_or_404(ticket_id: int) -> dict:
    ticket = tickets.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@app.get("/")
def root() -> dict:
    return {"service": "support-tickets", "version": APP_VERSION}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    return {"app": "support-tickets", "version": APP_VERSION}


@app.post("/tickets", status_code=201)
def create_ticket(payload: TicketCreate) -> Ticket:
    global _next_id
    now = _now()
    ticket: Ticket = Ticket(
        id=_next_id,
        status="open",
        created_at=now,
        updated_at=now,
        replies=[],
        **payload.model_dump(),
    )
    tickets[_next_id] = ticket
    _next_id += 1
    logger.info("Created ticket #%s from %s (%s)", ticket.id, ticket.email, ticket.name)
    return ticket


@app.get("/tickets", response_model=List[Ticket])
def list_tickets(status: Optional[str] = Query(None)) -> List[Ticket]:
    if status is not None:
        if status not in STATUSES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status '{status}'. Use one of {STATUSES}",
            )
        return [t for t in tickets.values() if t.status == status]
    return list(tickets.values())


@app.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: int) -> Ticket:
    return _get_ticket_or_404(ticket_id)


@app.post("/tickets/{ticket_id}/reply", response_model=Ticket)
def reply_to_ticket(ticket_id: int, payload: ReplyCreate) -> Ticket:
    if payload.status not in STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{payload.status}'. Use one of {STATUSES}",
        )
    ticket = _get_ticket_or_404(ticket_id)
    ticket.replies.append(
        {"message": payload.message, "replied_at": _now()}
    )
    ticket.status = payload.status
    ticket.updated_at = _now()
    logger.info("Ticket #%s moved to %s", ticket.id, ticket.status)
    return ticket


@app.get("/stats")
def stats() -> dict:
    counts = {s: 0 for s in STATUSES}
    for t in tickets.values():
        counts[t.status] += 1
    return {"total": len(tickets), "by_status": counts}
