from typing import Literal

from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    route: Literal["needs_retrieval", "general"]
    reasoning: str = Field(description="Brief justification for the routing decision")


class ChunkRelevance(BaseModel):
    chunk_index: int
    relevant: bool


class GradeResult(BaseModel):
    sufficient: bool = Field(
        description="Whether the retrieved chunks are sufficient to answer the question"
    )
    relevances: list[ChunkRelevance]


class Source(BaseModel):
    filename: str
    chunk_index: int
