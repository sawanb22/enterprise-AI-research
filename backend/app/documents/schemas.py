from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    filename: str
    file_hash: str
    file_size_bytes: int
    status: str
    page_count: int | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class DocumentDetailOut(DocumentOut):
    chunk_count: int = 0


class DocumentListOut(BaseModel):
    documents: list[DocumentOut]
    total: int


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    page_number: int
    chunk_index: int
    raw_text: str
    visual_summary: str = ""
    token_count: int
    created_at: datetime
