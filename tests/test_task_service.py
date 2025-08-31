import pytest
from app.database import reset_db
from app.task_service import TaskService
from app.models import TaskCreate, TaskUpdate


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


def test_create_task(new_db):
    """Test creating a new task"""
    task_data = TaskCreate(title="Buy groceries")
    task = TaskService.create_task(task_data)

    assert task.id is not None
    assert task.title == "Buy groceries"
    assert not task.completed
    assert task.created_at is not None


def test_get_all_tasks_empty(new_db):
    """Test getting tasks when database is empty"""
    tasks = TaskService.get_all_tasks()
    assert tasks == []


def test_get_all_tasks_with_data(new_db):
    """Test getting all tasks with data"""
    # Create some tasks
    TaskService.create_task(TaskCreate(title="Task 1"))
    TaskService.create_task(TaskCreate(title="Task 2"))
    TaskService.create_task(TaskCreate(title="Task 3"))

    tasks = TaskService.get_all_tasks()
    assert len(tasks) == 3
    # Should be ordered by creation date desc (newest first)
    assert tasks[0].title == "Task 3"
    assert tasks[1].title == "Task 2"
    assert tasks[2].title == "Task 1"


def test_get_task_by_id_exists(new_db):
    """Test getting a task that exists"""
    created_task = TaskService.create_task(TaskCreate(title="Find me"))

    if created_task.id is not None:
        found_task = TaskService.get_task_by_id(created_task.id)
        assert found_task is not None
        assert found_task.title == "Find me"
        assert found_task.id == created_task.id


def test_get_task_by_id_not_exists(new_db):
    """Test getting a task that doesn't exist"""
    task = TaskService.get_task_by_id(999)
    assert task is None


def test_update_task_title(new_db):
    """Test updating task title"""
    created_task = TaskService.create_task(TaskCreate(title="Original title"))

    if created_task.id is not None:
        update_data = TaskUpdate(title="Updated title")
        updated_task = TaskService.update_task(created_task.id, update_data)

        assert updated_task is not None
        assert updated_task.title == "Updated title"
        assert not updated_task.completed  # Should remain unchanged


def test_update_task_completion(new_db):
    """Test updating task completion status"""
    created_task = TaskService.create_task(TaskCreate(title="Complete me"))

    if created_task.id is not None:
        update_data = TaskUpdate(completed=True)
        updated_task = TaskService.update_task(created_task.id, update_data)

        assert updated_task is not None
        assert updated_task.completed
        assert updated_task.title == "Complete me"  # Should remain unchanged


def test_update_task_both_fields(new_db):
    """Test updating both title and completion"""
    created_task = TaskService.create_task(TaskCreate(title="Original"))

    if created_task.id is not None:
        update_data = TaskUpdate(title="Updated", completed=True)
        updated_task = TaskService.update_task(created_task.id, update_data)

        assert updated_task is not None
        assert updated_task.title == "Updated"
        assert updated_task.completed


def test_update_task_not_exists(new_db):
    """Test updating a task that doesn't exist"""
    update_data = TaskUpdate(title="Won't work")
    result = TaskService.update_task(999, update_data)
    assert result is None


def test_toggle_task_completion_false_to_true(new_db):
    """Test toggling task from incomplete to complete"""
    created_task = TaskService.create_task(TaskCreate(title="Toggle me"))

    if created_task.id is not None:
        toggled_task = TaskService.toggle_task_completion(created_task.id)

        assert toggled_task is not None
        assert toggled_task.completed


def test_toggle_task_completion_true_to_false(new_db):
    """Test toggling task from complete to incomplete"""
    created_task = TaskService.create_task(TaskCreate(title="Toggle me back"))

    if created_task.id is not None:
        # First toggle to complete
        TaskService.toggle_task_completion(created_task.id)
        # Then toggle back to incomplete
        toggled_task = TaskService.toggle_task_completion(created_task.id)

        assert toggled_task is not None
        assert not toggled_task.completed


def test_toggle_task_completion_not_exists(new_db):
    """Test toggling completion for task that doesn't exist"""
    result = TaskService.toggle_task_completion(999)
    assert result is None


def test_delete_task_exists(new_db):
    """Test deleting a task that exists"""
    created_task = TaskService.create_task(TaskCreate(title="Delete me"))

    if created_task.id is not None:
        result = TaskService.delete_task(created_task.id)
        assert result

        # Verify task is actually deleted
        deleted_task = TaskService.get_task_by_id(created_task.id)
        assert deleted_task is None


def test_delete_task_not_exists(new_db):
    """Test deleting a task that doesn't exist"""
    result = TaskService.delete_task(999)
    assert not result


def test_get_task_stats_empty(new_db):
    """Test task statistics with no tasks"""
    stats = TaskService.get_task_stats()
    assert stats == {"total": 0, "completed": 0, "pending": 0}


def test_get_task_stats_with_data(new_db):
    """Test task statistics with mixed completion states"""
    # Create tasks with different completion states
    task1 = TaskService.create_task(TaskCreate(title="Completed task"))
    TaskService.create_task(TaskCreate(title="Pending task 1"))
    TaskService.create_task(TaskCreate(title="Pending task 2"))

    # Complete one task
    if task1.id is not None:
        TaskService.toggle_task_completion(task1.id)

    stats = TaskService.get_task_stats()
    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["pending"] == 2


def test_task_title_validation(new_db):
    """Test that empty titles are handled properly"""
    # This test verifies the model validation works
    task_data = TaskCreate(title="")
    task = TaskService.create_task(task_data)
    assert task.title == ""  # Empty string should be allowed


def test_multiple_operations_sequence(new_db):
    """Test a realistic sequence of operations"""
    # Create multiple tasks
    task1 = TaskService.create_task(TaskCreate(title="Task 1"))
    task2 = TaskService.create_task(TaskCreate(title="Task 2"))
    task3 = TaskService.create_task(TaskCreate(title="Task 3"))

    # Complete some tasks
    if task1.id is not None:
        TaskService.toggle_task_completion(task1.id)
    if task3.id is not None:
        TaskService.toggle_task_completion(task3.id)

    # Update a task title
    if task2.id is not None:
        TaskService.update_task(task2.id, TaskUpdate(title="Updated Task 2"))

    # Verify final state
    all_tasks = TaskService.get_all_tasks()
    assert len(all_tasks) == 3

    stats = TaskService.get_task_stats()
    assert stats["total"] == 3
    assert stats["completed"] == 2
    assert stats["pending"] == 1

    # Find the updated task
    updated_task = next((t for t in all_tasks if t.title == "Updated Task 2"), None)
    assert updated_task is not None
    assert not updated_task.completed
