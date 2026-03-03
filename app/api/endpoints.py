"""API endpoints for upload, search, and auth."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.security import create_access_token, require_roles
from app.services.embeddings import ingest_directory
from app.services.llm_service import generate_answer
from app.services.retriever import retrieve_similar_chunks

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchResponse(BaseModel):
    answer: str
    sources: list[dict[str, str | int | float]]


class LoginRequest(BaseModel):
    username: str
    role: str = Field(default="User", pattern="^(Admin|User)$")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/token", response_model=LoginResponse)
def issue_token(payload: LoginRequest) -> LoginResponse:
    """Issue demonstration token with user-selected role."""

    token = create_access_token(username=payload.username, role=payload.role)
    return LoginResponse(access_token=token)


@router.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    _: dict[str, str] = Depends(require_roles("Admin")),
) -> dict[str, str | int]:
    """Upload source documents and trigger re-indexing."""

    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    accepted = {".txt", ".pdf"}
    saved = 0
    for upload in files:
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in accepted:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {upload.filename}")
        target = settings.data_dir / upload.filename
        data = await upload.read()
        target.write_bytes(data)
        saved += 1

    chunks = ingest_directory(settings.data_dir, settings.vector_store_dir)
    logger.info("Ingested %s chunks from %s uploaded files", chunks, saved)
    return {"message": "Upload and ingestion complete", "files_uploaded": saved, "chunks_indexed": chunks}


@router.get("/search", response_model=SearchResponse)
def search_documents(
    query: str = Query(..., min_length=2),
    _: dict[str, str] = Depends(require_roles("Admin", "User")),
) -> SearchResponse:
    """Perform vector retrieval and produce final answer with source refs."""

    hits = retrieve_similar_chunks(query=query, top_k=5)
    answer = generate_answer(query, hits)
    return SearchResponse(answer=answer, sources=hits)
