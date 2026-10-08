from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timezones import user_today
from app.models import Mark, StudyTask, Subject, Topic, User
from app.schemas.dashboard import DashboardSummary, SubjectPerformance
from app.schemas.exam import ExamOut
from app.services.exam_service import list_exams

GRADE_THRESHOLDS: list[tuple[float, str]] = [(80, "A"), (65, "B"), (50, "C"), (35, "D")]


def grade_for(percentage: float | None) -> str | None:
    if percentage is None:
        return None
    for threshold, grade in GRADE_THRESHOLDS:
        if percentage >= threshold:
            return grade
    return "F"


def _percent(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def _as_aware(dt: datetime) -> datetime:
    # sqlite drops the timezone, values are utc
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def subject_performance(db: Session, user: User) -> list[SubjectPerformance]:
    subjects = db.scalars(select(Subject).where(Subject.user_id == user.id).order_by(Subject.name))
    marks = db.scalars(select(Mark).where(Mark.user_id == user.id))
    by_subject: dict[int, list[float]] = {}
    for mark in marks:
        by_subject.setdefault(mark.subject_id, []).append(mark.score / mark.max_score * 100)
    return [
        SubjectPerformance(
            subject_id=s.id,
            subject=s.name,
            color=s.color,
            avg_percentage=round(sum(p) / len(p), 1) if (p := by_subject.get(s.id)) else None,
            target_score=s.target_score,
        )
        for s in subjects
    ]


def summary(db: Session, user: User) -> DashboardSummary:
    today = user_today(user)

    today_tasks = db.scalars(
        select(StudyTask).where(StudyTask.user_id == user.id, StudyTask.scheduled_date == today)
    ).all()

    upcoming = list_exams(db, user, upcoming=True)
    next_exam = upcoming[0] if upcoming else None

    topics = db.scalars(select(Topic).join(Subject).where(Subject.user_id == user.id)).all()
    completed = [t for t in topics if t.status == "completed"]
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    completed_this_week = [
        t for t in completed if t.completed_at and _as_aware(t.completed_at) >= week_ago
    ]

    marks = db.scalars(select(Mark).where(Mark.user_id == user.id)).all()
    avg_mark = (
        sum(m.score / m.max_score * 100 for m in marks) / len(marks) if marks else None
    )

    performance = subject_performance(db, user)
    weak = [
        p for p in performance
        if p.avg_percentage is not None and p.avg_percentage < p.target_score
    ]

    return DashboardSummary(
        today_tasks_total=len(today_tasks),
        today_tasks_completed=sum(1 for t in today_tasks if t.status == "completed"),
        days_to_next_exam=(next_exam.exam_date - today).days if next_exam else None,
        next_exam=ExamOut.model_validate(next_exam) if next_exam else None,
        overall_progress=_percent(len(completed), len(topics)),
        progress_change_this_week=_percent(len(completed_this_week), len(topics)),
        current_grade=grade_for(avg_mark),
        subject_performance=performance,
        weak_subjects=weak,
    )
