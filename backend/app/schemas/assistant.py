from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AssistantQuery(BaseModel):
    question: str = Field(..., min_length=3, description="用户输入的问题")
    provider: Optional[str] = Field(default=None, description="外部模型供应商")
    model: Optional[str] = Field(default=None, description="外部模型名称")


class Citation(BaseModel):
    title: str
    path: str


class AssistantReply(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    follow_up: List[str] = Field(default_factory=list)
    llm_used: bool = False
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    grounding_used: bool = False
    grounding_sources: List[str] = Field(default_factory=list)
    grounding_status: str = "none"
    validation_warnings: List[str] = Field(default_factory=list)
    referenced_entities: Dict = Field(default_factory=dict)


class AssistantModelOption(BaseModel):
    provider: str
    model: str
    label: str
    configured: bool


class AssistantProviderList(BaseModel):
    enabled: bool
    default_provider: str
    default_model: str
    options: List[AssistantModelOption] = Field(default_factory=list)
