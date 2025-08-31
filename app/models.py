from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Todo(SQLModel, table=True):
    """Model for storing to-do items."""

    __tablename__ = "todos"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TodoCreate(SQLModel, table=False):
    """Schema for creating new to-do items."""

    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class TodoUpdate(SQLModel, table=False):
    """Schema for updating existing to-do items."""

    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: Optional[bool] = Field(default=None)
