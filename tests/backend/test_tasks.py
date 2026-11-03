"""
Tests for task API endpoints (GET/POST /api/tasks, PATCH/DELETE /api/tasks/{id}).
"""
import itertools

import pytest

import main


@pytest.fixture(autouse=True)
def isolated_tasks(monkeypatch):
    """Give every test an empty task store and a fresh id counter.

    Tasks live in module-level memory, so without this tests would leak state
    into each other (and into the running app's data).
    """
    monkeypatch.setattr(main, "tasks_store", [])
    monkeypatch.setattr(main, "_task_ids", itertools.count(1))


def make_task(client, **overrides):
    payload = {"title": "Reorder gaskets", "priority": "high", "dueDate": "2025-10-15"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


class TestTaskEndpoints:
    """Test suite for task endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that the task list starts empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns 201 and the full task structure."""
        response = make_task(client)
        assert response.status_code == 201

        task = response.json()
        assert task["id"] == "task-1"
        assert task["title"] == "Reorder gaskets"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-15"
        assert task["status"] == "pending"

    def test_created_task_ids_are_strings(self, client):
        """Test ids are strings so they cannot collide with the frontend's integer mock task ids."""
        task = make_task(client).json()
        assert isinstance(task["id"], str)

    def test_create_task_trims_title(self, client):
        """Test that surrounding whitespace is stripped from the title."""
        task = make_task(client, title="  Call supplier  ").json()
        assert task["title"] == "Call supplier"

    def test_create_task_default_priority(self, client):
        """Test that priority defaults to medium when omitted."""
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2025-10-15"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_get_tasks_newest_first(self, client):
        """Test that tasks are returned newest first (the UI prepends new tasks)."""
        make_task(client, title="first")
        make_task(client, title="second")

        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_create_task_blank_title(self, client):
        """Test that a whitespace-only title is rejected."""
        response = make_task(client, title="   ")
        assert response.status_code == 400
        assert "title" in response.json()["detail"].lower()

    def test_create_task_empty_title(self, client):
        """Test that an empty title fails validation."""
        assert make_task(client, title="").status_code == 422

    def test_create_task_invalid_priority(self, client):
        """Test that an unknown priority fails validation."""
        assert make_task(client, priority="urgent").status_code == 422

    def test_create_task_invalid_due_date(self, client):
        """Test that a malformed or impossible due date is rejected."""
        # "2025-1-5" is unpadded: strptime would accept it, but it is not YYYY-MM-DD
        for bad_date in ["not-a-date", "10/15/2025", "2025-02-30", "2025-1-5"]:
            response = make_task(client, dueDate=bad_date)
            assert response.status_code == 400, bad_date
            assert "duedate" in response.json()["detail"].lower()

    def test_create_task_missing_due_date(self, client):
        """Test that dueDate is required."""
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """Test toggling a task completes it and toggling again reopens it."""
        task_id = make_task(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_toggle_persists(self, client):
        """Test that a toggle is visible on the next list call."""
        task_id = make_task(client).json()["id"]
        client.patch(f"/api/tasks/{task_id}")

        tasks = client.get("/api/tasks").json()
        assert tasks[0]["status"] == "completed"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task_id = make_task(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert "message" in response.json()
        assert client.get("/api/tasks").json() == []

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_task_ids_not_reused_after_delete(self, client):
        """Test that deleting a task never causes its id to be reissued."""
        first = make_task(client).json()["id"]
        client.delete(f"/api/tasks/{first}")
        second = make_task(client).json()["id"]
        assert second != first
