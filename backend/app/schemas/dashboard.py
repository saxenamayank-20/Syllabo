from pydantic import BaseModel

from app.schemas.exam import ExamOut


class SubjectPerformance(BaseModel):
    subject_id: int
    subject: str
    color: str
    avg_percentage: float | None
    target_score: int


class DashboardSummary(BaseModel):
    today_tasks_total: int
    today_tasks_completed: int
    days_to_next_exam: int | None
    next_exam: ExamOut | None
    overall_progress: float
    progress_change_this_week: float
    current_grade: str | None
    subject_performance: list[SubjectPerformance]
    weak_subjects: list[SubjectPerformance]
