from nicegui import ui
from app.task_service import TaskService
from app.models import TaskCreate, TaskUpdate
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TodoApp:
    """Main Todo Application UI Component"""

    def __init__(self):
        self.tasks_container = None
        self.stats_container = None
        self.new_task_input = None
        self.edit_dialog = None
        self.edit_input = None
        self.edit_task_id: Optional[int] = None

    def create_ui(self):
        """Create the main todo application UI"""
        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        # Main container with modern styling
        with ui.column().classes("w-full max-w-4xl mx-auto p-6 bg-gray-50 min-h-screen"):
            self._create_header()
            self._create_add_task_form()
            self._create_stats_section()
            self._create_task_list()
            self._create_edit_dialog()

        # Initial load
        self._refresh_ui()

    def _create_header(self):
        """Create the application header"""
        with ui.card().classes("w-full p-6 bg-white shadow-lg rounded-xl mb-6"):
            ui.label("📋 Todo Application").classes("text-3xl font-bold text-gray-800 text-center")
            ui.label("Organize your tasks efficiently").classes("text-lg text-gray-600 text-center mt-2")

    def _create_add_task_form(self):
        """Create the form to add new tasks"""
        with ui.card().classes("w-full p-6 bg-white shadow-lg rounded-xl mb-6"):
            ui.label("Add New Task").classes("text-xl font-semibold text-gray-800 mb-4")

            with ui.row().classes("w-full gap-4"):
                self.new_task_input = (
                    ui.input(placeholder="Enter task title...").classes("flex-1").props("outlined clearable")
                )

                ui.button("Add Task", on_click=self._add_task, icon="add").classes("bg-primary text-white px-6 py-2")

            # Allow Enter key to submit
            self.new_task_input.on("keydown.enter", self._add_task)

    def _create_stats_section(self):
        """Create the statistics display"""
        self.stats_container = ui.row().classes("w-full gap-4 mb-6")

    def _create_task_list(self):
        """Create the task list container"""
        with ui.card().classes("w-full p-6 bg-white shadow-lg rounded-xl"):
            ui.label("Your Tasks").classes("text-xl font-semibold text-gray-800 mb-4")
            self.tasks_container = ui.column().classes("w-full gap-3")

    def _create_edit_dialog(self):
        """Create the edit task dialog"""
        with ui.dialog() as self.edit_dialog, ui.card().classes("w-96"):
            ui.label("Edit Task").classes("text-xl font-semibold mb-4")

            self.edit_input = ui.input(label="Task Title").classes("w-full mb-4").props("outlined")

            with ui.row().classes("w-full gap-2 justify-end"):
                ui.button("Cancel", on_click=lambda: self.edit_dialog.close() if self.edit_dialog else None).props(
                    "outline"
                )

                ui.button("Save", on_click=self._save_edit).classes("bg-primary text-white")

    def _add_task(self):
        """Add a new task"""
        if self.new_task_input is None:
            return

        title = self.new_task_input.value.strip()
        if not title:
            ui.notify("Please enter a task title", type="warning")
            return

        try:
            task_data = TaskCreate(title=title)
            TaskService.create_task(task_data)
            self.new_task_input.value = ""
            self._refresh_ui()
            ui.notify("Task added successfully!", type="positive")
        except Exception as e:
            logger.error(f"Error adding task: {str(e)}")
            ui.notify(f"Error adding task: {str(e)}", type="negative")

    def _toggle_task(self, task_id: int):
        """Toggle task completion status"""
        try:
            result = TaskService.toggle_task_completion(task_id)
            if result:
                self._refresh_ui()
                status = "completed" if result.completed else "pending"
                ui.notify(f"Task marked as {status}", type="positive")
            else:
                ui.notify("Task not found", type="negative")
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            ui.notify(f"Error updating task: {str(e)}", type="negative")

    def _edit_task(self, task_id: int):
        """Open edit dialog for a task"""
        task = TaskService.get_task_by_id(task_id)
        if task is None:
            ui.notify("Task not found", type="negative")
            return

        self.edit_task_id = task_id
        if self.edit_input:
            self.edit_input.value = task.title
        if self.edit_dialog:
            self.edit_dialog.open()

    def _save_edit(self):
        """Save the edited task"""
        if self.edit_task_id is None or self.edit_input is None:
            return

        title = self.edit_input.value.strip()
        if not title:
            ui.notify("Please enter a task title", type="warning")
            return

        try:
            update_data = TaskUpdate(title=title)
            result = TaskService.update_task(self.edit_task_id, update_data)
            if result:
                self._refresh_ui()
                ui.notify("Task updated successfully!", type="positive")
                if self.edit_dialog:
                    self.edit_dialog.close()
            else:
                ui.notify("Task not found", type="negative")
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            ui.notify(f"Error updating task: {str(e)}", type="negative")
        finally:
            self.edit_task_id = None

    def _delete_task(self, task_id: int):
        """Delete a task with confirmation"""

        async def confirm_delete():
            with ui.dialog() as dialog, ui.card():
                ui.label("Confirm Delete").classes("text-xl font-semibold mb-4")
                ui.label("Are you sure you want to delete this task?").classes("mb-4")

                with ui.row().classes("gap-2 justify-end"):
                    ui.button("Cancel", on_click=lambda: dialog.close()).props("outline")
                    ui.button("Delete", on_click=lambda: dialog.submit(True)).classes("bg-negative text-white")

            result = await dialog
            if result:
                try:
                    success = TaskService.delete_task(task_id)
                    if success:
                        self._refresh_ui()
                        ui.notify("Task deleted successfully!", type="positive")
                    else:
                        ui.notify("Task not found", type="negative")
                except Exception as e:
                    logger.error(f"Error deleting task: {str(e)}")
                    ui.notify(f"Error deleting task: {str(e)}", type="negative")

        import asyncio

        asyncio.create_task(confirm_delete())

    def _refresh_ui(self):
        """Refresh the entire UI with current data"""
        self._refresh_stats()
        self._refresh_tasks()

    def _refresh_stats(self):
        """Refresh the statistics display"""
        if self.stats_container is None:
            return

        self.stats_container.clear()

        with self.stats_container:
            stats = TaskService.get_task_stats()

            # Total tasks card
            with ui.card().classes("p-4 bg-blue-50 border border-blue-200 rounded-lg flex-1"):
                ui.label("Total Tasks").classes("text-sm text-gray-600 uppercase")
                ui.label(str(stats["total"])).classes("text-2xl font-bold text-blue-600 mt-1")

            # Completed tasks card
            with ui.card().classes("p-4 bg-green-50 border border-green-200 rounded-lg flex-1"):
                ui.label("Completed").classes("text-sm text-gray-600 uppercase")
                ui.label(str(stats["completed"])).classes("text-2xl font-bold text-green-600 mt-1")

            # Pending tasks card
            with ui.card().classes("p-4 bg-orange-50 border border-orange-200 rounded-lg flex-1"):
                ui.label("Pending").classes("text-sm text-gray-600 uppercase")
                ui.label(str(stats["pending"])).classes("text-2xl font-bold text-orange-600 mt-1")

    def _refresh_tasks(self):
        """Refresh the task list display"""
        if self.tasks_container is None:
            return

        self.tasks_container.clear()

        with self.tasks_container:
            tasks = TaskService.get_all_tasks()

            if not tasks:
                with ui.card().classes("p-6 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg text-center"):
                    ui.icon("assignment").classes("text-4xl text-gray-400 mb-2")
                    ui.label("No tasks yet").classes("text-xl text-gray-500 font-medium")
                    ui.label("Add your first task above to get started!").classes("text-gray-400")
                return

            for task in tasks:
                self._create_task_item(task)

    def _create_task_item(self, task):
        """Create a single task item in the list"""
        if task.id is None:
            return

        task_id = task.id
        completed_class = "bg-green-50 border-green-200" if task.completed else "bg-white border-gray-200"
        text_class = "line-through text-gray-500" if task.completed else "text-gray-800"

        with ui.card().classes(f"p-4 {completed_class} border rounded-lg"):
            with ui.row().classes("w-full items-center gap-4"):
                # Completion checkbox
                ui.checkbox(value=task.completed, on_change=lambda: self._toggle_task(task_id)).classes("text-primary")

                # Task title
                ui.label(task.title).classes(f"flex-1 text-lg {text_class}")

                # Created date
                created_date = task.created_at.strftime("%m/%d %H:%M")
                ui.label(created_date).classes("text-sm text-gray-400")

                # Action buttons
                with ui.row().classes("gap-1"):
                    ui.button(icon="edit", on_click=lambda: self._edit_task(task_id)).classes("p-2").props(
                        "flat round size=sm color=primary"
                    )

                    ui.button(icon="delete", on_click=lambda: self._delete_task(task_id)).classes("p-2").props(
                        "flat round size=sm color=negative"
                    )


def create():
    """Create and register the todo application"""

    @ui.page("/")
    def todo_page():
        app = TodoApp()
        app.create_ui()
