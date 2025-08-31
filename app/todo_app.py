"""To-Do application UI module."""

import logging
from nicegui import ui

from app.models import TodoCreate, TodoUpdate
from app.todo_service import (
    create_todo,
    get_all_todos,
    toggle_todo_completion,
    delete_todo,
    update_todo,
)

logger = logging.getLogger(__name__)


def create():
    """Create the To-Do application UI."""

    @ui.page("/")
    def todo_page():
        # Apply modern theme colors
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        # Main container
        with ui.column().classes("w-full max-w-4xl mx-auto p-6"):
            # Header
            ui.label("My To-Do List").classes("text-3xl font-bold text-gray-800 mb-6")

            # Add new todo section
            with ui.card().classes("w-full p-6 mb-6 shadow-lg rounded-xl"):
                ui.label("Add New Task").classes("text-lg font-semibold text-gray-700 mb-4")

                with ui.row().classes("w-full gap-4"):
                    title_input = ui.input(placeholder="Enter task title...").classes("flex-1")
                    title_input.props("outlined")

                with ui.row().classes("w-full gap-4 mt-2"):
                    description_input = ui.textarea(placeholder="Optional description...").classes("flex-1")
                    description_input.props("outlined rows=2")

                with ui.row().classes("justify-end mt-4"):
                    add_button = ui.button("Add Task", icon="add").classes("bg-primary text-white px-6 py-2")

            # Todo list container
            todo_container = ui.column().classes("w-full gap-2")

        def refresh_todos():
            """Refresh the todo list display."""
            todo_container.clear()
            todos = get_all_todos()

            if not todos:
                with todo_container:
                    with ui.card().classes("w-full p-8 text-center bg-gray-50"):
                        ui.icon("inbox", size="48px").classes("text-gray-400 mb-4")
                        ui.label("No tasks yet").classes("text-xl text-gray-500 mb-2")
                        ui.label("Add your first task above to get started!").classes("text-gray-400")
                return

            # Group todos by status
            pending_todos = [todo for todo in todos if not todo.completed]
            completed_todos = [todo for todo in todos if todo.completed]

            with todo_container:
                # Pending todos section
                if pending_todos:
                    ui.label("Pending Tasks").classes("text-lg font-semibold text-gray-700 mb-2 mt-4")
                    for todo in pending_todos:
                        create_todo_card(todo)

                # Completed todos section
                if completed_todos:
                    ui.label("Completed Tasks").classes("text-lg font-semibold text-gray-700 mb-2 mt-6")
                    for todo in completed_todos:
                        create_todo_card(todo)

        def create_todo_card(todo):
            """Create a card for a single todo item."""
            card_classes = "w-full p-4 mb-2 shadow-md rounded-lg hover:shadow-lg transition-shadow"
            if todo.completed:
                card_classes += " bg-gray-50 border-l-4 border-green-400"
            else:
                card_classes += " bg-white border-l-4 border-blue-400"

            with ui.card().classes(card_classes):
                with ui.row().classes("w-full justify-between items-start"):
                    # Left side - todo content
                    with ui.column().classes("flex-1"):
                        title_classes = "text-lg font-medium"
                        if todo.completed:
                            title_classes += " line-through text-gray-500"
                        else:
                            title_classes += " text-gray-800"

                        ui.label(todo.title).classes(title_classes)

                        if todo.description:
                            desc_classes = "text-sm mt-1"
                            if todo.completed:
                                desc_classes += " text-gray-400"
                            else:
                                desc_classes += " text-gray-600"
                            ui.label(todo.description).classes(desc_classes)

                        # Timestamp
                        time_classes = "text-xs mt-2"
                        if todo.completed:
                            time_classes += " text-gray-400"
                        else:
                            time_classes += " text-gray-500"
                        ui.label(f"Created: {todo.created_at.strftime('%Y-%m-%d %H:%M')}").classes(time_classes)

                    # Right side - action buttons
                    with ui.column().classes("gap-2"):
                        # Toggle completion button
                        if todo.completed:
                            toggle_btn = ui.button(icon="undo", on_click=lambda _, t_id=todo.id: handle_toggle(t_id))
                            toggle_btn.classes("bg-gray-500 text-white").props("round size=sm")
                            toggle_btn.tooltip("Mark as incomplete")
                        else:
                            toggle_btn = ui.button(icon="check", on_click=lambda _, t_id=todo.id: handle_toggle(t_id))
                            toggle_btn.classes("bg-green-500 text-white").props("round size=sm")
                            toggle_btn.tooltip("Mark as complete")

                        # Edit button
                        edit_btn = ui.button(icon="edit", on_click=lambda _, t_id=todo.id: handle_edit(t_id))
                        edit_btn.classes("bg-blue-500 text-white").props("round size=sm")
                        edit_btn.tooltip("Edit task")

                        # Delete button
                        delete_btn = ui.button(icon="delete", on_click=lambda _, t_id=todo.id: handle_delete(t_id))
                        delete_btn.classes("bg-red-500 text-white").props("round size=sm")
                        delete_btn.tooltip("Delete task")

        def handle_add():
            """Handle adding a new todo."""
            title = title_input.value.strip()
            if not title:
                ui.notify("Please enter a task title", type="negative")
                return

            try:
                todo_data = TodoCreate(title=title, description=description_input.value.strip() or None)
                create_todo(todo_data)

                # Clear inputs
                title_input.value = ""
                description_input.value = ""

                # Refresh display
                refresh_todos()
                ui.notify("Task added successfully!", type="positive")

            except Exception as e:
                logger.error(f"Error adding task: {str(e)}")
                ui.notify(f"Error adding task: {str(e)}", type="negative")

        def handle_toggle(todo_id: int):
            """Handle toggling todo completion status."""
            try:
                result = toggle_todo_completion(todo_id)
                if result:
                    refresh_todos()
                    status = "completed" if result.completed else "marked as pending"
                    ui.notify(f"Task {status}!", type="positive")
                else:
                    ui.notify("Task not found", type="negative")
            except Exception as e:
                logger.error(f"Error updating task: {str(e)}")
                ui.notify(f"Error updating task: {str(e)}", type="negative")

        async def handle_delete(todo_id: int):
            """Handle deleting a todo with confirmation."""
            try:
                with ui.dialog() as delete_dialog, ui.card():
                    ui.label("Are you sure you want to delete this task?")
                    with ui.row():
                        ui.button("Yes", on_click=lambda: delete_dialog.submit("Yes"))
                        ui.button("No", on_click=lambda: delete_dialog.submit("No"))

                result = await delete_dialog
                if result == "Yes":
                    success = delete_todo(todo_id)
                    if success:
                        refresh_todos()
                        ui.notify("Task deleted successfully!", type="positive")
                    else:
                        ui.notify("Task not found", type="negative")
            except Exception as e:
                logger.error(f"Error deleting task: {str(e)}")
                ui.notify(f"Error deleting task: {str(e)}", type="negative")

        async def handle_edit(todo_id: int):
            """Handle editing a todo item."""
            try:
                # Get current todo
                from app.todo_service import get_todo

                current_todo = get_todo(todo_id)
                if not current_todo:
                    ui.notify("Task not found", type="negative")
                    return

                # Create edit dialog
                with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
                    ui.label("Edit Task").classes("text-xl font-bold mb-4")

                    edit_title = ui.input("Title", value=current_todo.title).classes("w-full mb-4")
                    edit_title.props("outlined")

                    edit_description = ui.textarea("Description", value=current_todo.description or "").classes(
                        "w-full mb-4"
                    )
                    edit_description.props("outlined rows=3")

                    save_clicked = False

                    def on_save():
                        nonlocal save_clicked
                        save_clicked = True
                        dialog.close()

                    with ui.row().classes("gap-2 justify-end"):
                        ui.button("Cancel", on_click=dialog.close).props("outline")
                        ui.button("Save", on_click=on_save).classes("bg-primary text-white")

                dialog.open()
                await dialog

                if save_clicked:
                    new_title = edit_title.value.strip()
                    if not new_title:
                        ui.notify("Title cannot be empty", type="negative")
                        return

                    update_data = TodoUpdate(title=new_title, description=edit_description.value.strip() or None)

                    updated_todo = update_todo(todo_id, update_data)
                    if updated_todo:
                        refresh_todos()
                        ui.notify("Task updated successfully!", type="positive")
                    else:
                        ui.notify("Error updating task", type="negative")

            except Exception as e:
                logger.error(f"Error editing task: {str(e)}")
                ui.notify(f"Error editing task: {str(e)}", type="negative")

        # Wire up the add button
        add_button.on_click(handle_add)

        # Allow Enter key in title input to add todo
        title_input.on("keydown.enter", lambda _: handle_add())

        # Initial load
        refresh_todos()
