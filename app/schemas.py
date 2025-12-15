from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KnowledgeBaseCreate(BaseModel):
    question: str
    answer: str


class KnowledgeBaseResponse(BaseModel):
    id: int
    question: str
    answer: str

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str]


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class IssueCreate(BaseModel):
    title: str
    category_id: int
    knowledge_id: Optional[int]


class IssueResponse(BaseModel):
    id: int
    title: str
    category_id: int
    knowledge_id: Optional[int]

    class Config:
        from_attributes = True


class ChatLogResponse(BaseModel):
    id: int
    user_message: str
    bot_response: str
    created_at: datetime

    class Config:
        from_attributes = True