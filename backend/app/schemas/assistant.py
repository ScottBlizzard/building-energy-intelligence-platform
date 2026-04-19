from typing import List

from pydantic import BaseModel, Field


class AssistantQuery(BaseModel):
    question: str = Field(..., min_length=3, description="用户输入的问题")


class Citation(BaseModel):
    title: str
    path: str


class AssistantReply(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    follow_up: List[str] = Field(default_factory=list)

