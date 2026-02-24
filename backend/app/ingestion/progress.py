"""
Progress tracking for long-running ingestion tasks.
Uses in-memory storage with thread-safe access.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from threading import Lock
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    STORING = "storing"
    GRAPH_BUILDING = "graph_building"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskProgress:
    """Progress information for an ingestion task."""

    task_id: str
    filename: str
    status: TaskStatus = TaskStatus.PENDING
    total_pages: int = 0
    parsed_pages: int = 0
    total_chunks: int = 0
    embedded_chunks: int = 0
    stored_chunks: int = 0
    entities_extracted: int = 0
    edges_created: int = 0
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    # Low memory mode tracking
    current_batch: int = 0
    total_batches: int = 0
    streaming_mode: bool = False

    @property
    def progress_percent(self) -> float:
        """Calculate overall progress percentage (0-100)."""
        if self.status == TaskStatus.COMPLETED:
            return 100.0
        if self.status == TaskStatus.FAILED:
            return 0.0

        # Weight each stage
        weights = {
            TaskStatus.PENDING: 0,
            TaskStatus.PARSING: 0.3,
            TaskStatus.EMBEDDING: 0.5,
            TaskStatus.STORING: 0.15,
            TaskStatus.GRAPH_BUILDING: 0.05,
        }

        progress = 0.0

        # Parsing progress (30%)
        if self.total_pages > 0:
            parsing_progress = self.parsed_pages / self.total_pages
            progress += parsing_progress * weights[TaskStatus.PARSING] * 100

        # Embedding progress (50%)
        if self.total_chunks > 0:
            embedding_progress = self.embedded_chunks / self.total_chunks
            progress += embedding_progress * weights[TaskStatus.EMBEDDING] * 100

        # Storing progress (15%)
        if self.total_chunks > 0:
            storing_progress = self.stored_chunks / self.total_chunks
            progress += storing_progress * weights[TaskStatus.STORING] * 100

        # Graph building is fast, just add 5% if we're past storing
        if self.status == TaskStatus.GRAPH_BUILDING:
            progress += weights[TaskStatus.GRAPH_BUILDING] * 100

        return min(progress, 99.9)  # Cap at 99.9 until completed

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "task_id": self.task_id,
            "filename": self.filename,
            "status": self.status.value,
            "progress_percent": round(self.progress_percent, 1),
            "total_pages": self.total_pages,
            "parsed_pages": self.parsed_pages,
            "total_chunks": self.total_chunks,
            "embedded_chunks": self.embedded_chunks,
            "stored_chunks": self.stored_chunks,
            "entities_extracted": self.entities_extracted,
            "edges_created": self.edges_created,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_seconds": (
                (self.completed_at or datetime.utcnow()) - self.started_at
            ).total_seconds(),
            # Low memory mode info
            "streaming_mode": self.streaming_mode,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
        }


class ProgressTracker:
    """Thread-safe progress tracker for ingestion tasks."""

    def __init__(self):
        self._tasks: Dict[str, TaskProgress] = {}
        self._lock = Lock()

    def create_task(self, filename: str) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = TaskProgress(
                task_id=task_id,
                filename=filename,
            )
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> None:
        """Update task progress fields."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)

    def set_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status."""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = status
                if status == TaskStatus.COMPLETED:
                    self._tasks[task_id].completed_at = datetime.utcnow()

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed with error message."""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].error_message = error
                self._tasks[task_id].completed_at = datetime.utcnow()

    def increment(self, task_id: str, field: str, amount: int = 1) -> None:
        """Increment a counter field."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if hasattr(task, field):
                    current = getattr(task, field)
                    setattr(task, field, current + amount)

    def get_all_tasks(self) -> Dict[str, Dict]:
        """Get all tasks as dictionaries."""
        with self._lock:
            return {
                task_id: task.to_dict()
                for task_id, task in self._tasks.items()
            }

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Remove tasks older than max_age_hours. Returns count removed."""
        now = datetime.utcnow()
        removed = 0
        with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                age = (now - task.started_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(task_id)
            for task_id in to_remove:
                del self._tasks[task_id]
                removed += 1
        return removed


# Global singleton
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
