"""Service layer for To-Do operations."""

from datetime import datetime
from typing import Optional

from sqlmodel import select, desc, not_

from app.database import get_session
from app.models import Todo, TodoCreate, TodoUpdate


def create_todo(todo_data: TodoCreate) -> Todo:
    """Create a new to-do item."""
    with get_session() as session:
        todo = Todo(
            title=todo_data.title,
            description=todo_data.description,
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def get_all_todos() -> list[Todo]:
    """Get all to-do items."""
    with get_session() as session:
        statement = select(Todo).order_by(desc(Todo.created_at))
        result = session.exec(statement)
        return list(result.all())


def get_todo(todo_id: int) -> Optional[Todo]:
    """Get a to-do item by ID."""
    with get_session() as session:
        return session.get(Todo, todo_id)


def update_todo(todo_id: int, todo_data: TodoUpdate) -> Optional[Todo]:
    """Update a to-do item."""
    with get_session() as session:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return None

        # Update only provided fields
        if todo_data.title is not None:
            todo.title = todo_data.title
        if todo_data.description is not None:
            todo.description = todo_data.description
        if todo_data.completed is not None:
            todo.completed = todo_data.completed

        todo.updated_at = datetime.utcnow()
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def toggle_todo_completion(todo_id: int) -> Optional[Todo]:
    """Toggle the completion status of a to-do item."""
    with get_session() as session:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return None

        todo.completed = not todo.completed
        todo.updated_at = datetime.utcnow()
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def delete_todo(todo_id: int) -> bool:
    """Delete a to-do item. Returns True if deleted, False if not found."""
    with get_session() as session:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return False

        session.delete(todo)
        session.commit()
        return True


def get_completed_todos() -> list[Todo]:
    """Get all completed to-do items."""
    with get_session() as session:
        statement = select(Todo).where(Todo.completed).order_by(desc(Todo.updated_at))
        result = session.exec(statement)
        return list(result.all())


def get_pending_todos() -> list[Todo]:
    """Get all pending (incomplete) to-do items."""
    with get_session() as session:
        statement = select(Todo).where(not_(Todo.completed)).order_by(desc(Todo.created_at))
        result = session.exec(statement)
        return list(result.all())
