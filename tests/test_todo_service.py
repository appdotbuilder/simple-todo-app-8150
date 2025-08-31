"""Tests for the todo service layer."""

import pytest
from datetime import datetime

from app.database import reset_db
from app.models import TodoCreate, TodoUpdate
from app.todo_service import (
    create_todo,
    get_all_todos,
    get_todo,
    update_todo,
    toggle_todo_completion,
    delete_todo,
    get_completed_todos,
    get_pending_todos,
)


@pytest.fixture()
def new_db():
    """Fixture to provide a fresh database for each test."""
    reset_db()
    yield
    reset_db()


def test_create_todo(new_db):
    """Test creating a new to-do item."""
    todo_data = TodoCreate(title="Test Todo", description="Test description")
    todo = create_todo(todo_data)

    assert todo.id is not None
    assert todo.title == "Test Todo"
    assert todo.description == "Test description"
    assert not todo.completed
    assert isinstance(todo.created_at, datetime)
    assert isinstance(todo.updated_at, datetime)


def test_create_todo_without_description(new_db):
    """Test creating a to-do item without description."""
    todo_data = TodoCreate(title="Simple Todo")
    todo = create_todo(todo_data)

    assert todo.title == "Simple Todo"
    assert todo.description is None
    assert not todo.completed


def test_get_all_todos_empty(new_db):
    """Test getting all todos when database is empty."""
    todos = get_all_todos()
    assert todos == []


def test_get_all_todos_with_items(new_db):
    """Test getting all todos when items exist."""
    # Create multiple todos
    create_todo(TodoCreate(title="First Todo"))
    create_todo(TodoCreate(title="Second Todo"))
    create_todo(TodoCreate(title="Third Todo"))

    todos = get_all_todos()
    assert len(todos) == 3

    # Should be ordered by created_at desc (newest first)
    assert todos[0].title == "Third Todo"
    assert todos[1].title == "Second Todo"
    assert todos[2].title == "First Todo"


def test_get_todo_exists(new_db):
    """Test getting a specific todo that exists."""
    created_todo = create_todo(TodoCreate(title="Test Todo"))

    assert created_todo.id is not None
    retrieved_todo = get_todo(created_todo.id)
    assert retrieved_todo is not None
    assert retrieved_todo is not None
    assert retrieved_todo.id == created_todo.id
    assert retrieved_todo.title == "Test Todo"


def test_get_todo_not_exists(new_db):
    """Test getting a specific todo that doesn't exist."""
    todo = get_todo(999)
    assert todo is None


def test_update_todo_all_fields(new_db):
    """Test updating all fields of a todo."""
    todo = create_todo(TodoCreate(title="Original Title", description="Original description"))

    update_data = TodoUpdate(title="Updated Title", description="Updated description", completed=True)

    assert todo.id is not None
    updated_todo = update_todo(todo.id, update_data)
    assert updated_todo is not None
    assert updated_todo.title == "Updated Title"
    assert updated_todo.description == "Updated description"
    assert updated_todo.completed
    assert updated_todo.updated_at > todo.updated_at


def test_update_todo_partial_fields(new_db):
    """Test updating only some fields of a todo."""
    todo = create_todo(TodoCreate(title="Original Title", description="Original description"))

    # Update only title
    update_data = TodoUpdate(title="Updated Title")
    assert todo.id is not None
    updated_todo = update_todo(todo.id, update_data)

    assert updated_todo is not None
    assert updated_todo.title == "Updated Title"
    assert updated_todo.description == "Original description"  # Should remain unchanged
    assert not updated_todo.completed  # Should remain unchanged


def test_update_todo_not_exists(new_db):
    """Test updating a todo that doesn't exist."""
    update_data = TodoUpdate(title="Updated Title")
    result = update_todo(999, update_data)
    assert result is None


def test_toggle_todo_completion(new_db):
    """Test toggling completion status of a todo."""
    todo = create_todo(TodoCreate(title="Test Todo"))
    assert not todo.completed

    # Toggle to completed
    assert todo.id is not None
    toggled_todo = toggle_todo_completion(todo.id)
    assert toggled_todo is not None
    assert toggled_todo.completed

    # Toggle back to incomplete
    assert todo.id is not None
    toggled_again = toggle_todo_completion(todo.id)
    assert toggled_again is not None
    assert not toggled_again.completed


def test_toggle_todo_completion_not_exists(new_db):
    """Test toggling completion of a todo that doesn't exist."""
    result = toggle_todo_completion(999)
    assert result is None


def test_delete_todo_exists(new_db):
    """Test deleting a todo that exists."""
    todo = create_todo(TodoCreate(title="To be deleted"))

    assert todo.id is not None
    result = delete_todo(todo.id)
    assert result

    # Verify it's actually deleted
    deleted_todo = get_todo(todo.id)
    assert deleted_todo is None


def test_delete_todo_not_exists(new_db):
    """Test deleting a todo that doesn't exist."""
    result = delete_todo(999)
    assert not result


def test_get_completed_todos(new_db):
    """Test getting only completed todos."""
    # Create mixed todos
    todo1 = create_todo(TodoCreate(title="Completed Todo 1"))
    create_todo(TodoCreate(title="Incomplete Todo"))
    todo3 = create_todo(TodoCreate(title="Completed Todo 2"))

    # Mark some as completed
    assert todo1.id is not None
    assert todo3.id is not None
    toggle_todo_completion(todo1.id)
    toggle_todo_completion(todo3.id)

    completed_todos = get_completed_todos()
    assert len(completed_todos) == 2

    completed_titles = {todo.title for todo in completed_todos}
    assert "Completed Todo 1" in completed_titles
    assert "Completed Todo 2" in completed_titles
    assert "Incomplete Todo" not in completed_titles


def test_get_pending_todos(new_db):
    """Test getting only pending (incomplete) todos."""
    # Create mixed todos
    todo1 = create_todo(TodoCreate(title="Completed Todo"))
    create_todo(TodoCreate(title="Incomplete Todo 1"))
    create_todo(TodoCreate(title="Incomplete Todo 2"))

    # Mark one as completed
    assert todo1.id is not None
    toggle_todo_completion(todo1.id)

    pending_todos = get_pending_todos()
    assert len(pending_todos) == 2

    pending_titles = {todo.title for todo in pending_todos}
    assert "Incomplete Todo 1" in pending_titles
    assert "Incomplete Todo 2" in pending_titles
    assert "Completed Todo" not in pending_titles


def test_get_completed_todos_empty(new_db):
    """Test getting completed todos when none are completed."""
    create_todo(TodoCreate(title="Incomplete Todo"))

    completed_todos = get_completed_todos()
    assert completed_todos == []


def test_get_pending_todos_empty(new_db):
    """Test getting pending todos when all are completed."""
    todo = create_todo(TodoCreate(title="Todo"))
    assert todo.id is not None
    toggle_todo_completion(todo.id)

    pending_todos = get_pending_todos()
    assert pending_todos == []


def test_create_todo_with_long_title(new_db):
    """Test creating todo with maximum length title."""
    long_title = "A" * 200  # Max length from model
    todo_data = TodoCreate(title=long_title)
    todo = create_todo(todo_data)

    assert todo.title == long_title


def test_create_todo_with_long_description(new_db):
    """Test creating todo with maximum length description."""
    long_description = "B" * 1000  # Max length from model
    todo_data = TodoCreate(title="Test", description=long_description)
    todo = create_todo(todo_data)

    assert todo.description == long_description
