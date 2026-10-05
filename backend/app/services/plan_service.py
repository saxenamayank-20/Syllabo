"""AI study plan generation: build the prompt, validate Gemini's answer, map it to real IDs, save."""

import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.timezones import user_today
from app.models import StudyPlan, StudyPreference, StudyTask, Subject, User
from app.schemas.ai import (
    AIPlan,
    GeneratePlanRequest,
    PlanDayPreview,
    PlanPreview,
    PlanTaskIn,
    PlanTaskPreview,
    SavePlanRequest,
    SavePlanResponse,
    SkippedItem,
)
from app.schemas.preference import VALID_DAYS
from app.services import gemini_service, preference_service
from app.services.dashboard_service import subject_performance
from app.services.exam_service import list_exams

logger = logging.getLogger("studyai.plan")

PROMPT_TEMPLATE = """You are an expert study planner for a student. Create a day-by-day study plan.

Respond with JSON ONLY (no markdown, no commentary) in exactly this format:
{{"days":[{{"date":"YYYY-MM-DD","tasks":[{{"subject":"...","topic":"...","title":"...","start_time":"HH:MM","duration_mins":60}}]}}]}}

PLAN PERIOD: {start} to {end} (inclusive). Today is {today}.
ALLOWED STUDY DAYS: {study_days}. Only include dates in the period that fall on these weekdays.
DAILY STUDY LIMIT: {daily} minutes per day in total. Some days already have other tasks; the
minutes still available for each allowed date are:
{availability}

STUDENT'S GOAL: {goal}

SUBJECTS AND PENDING TOPICS (use these names exactly):
{subjects}

UPCOMING EXAMS:
{exams}

PERFORMANCE (average mark vs target):
{performance}

ALREADY SCHEDULED (keep clear of these times):
{existing}

RULES:
1. Never exceed the available minutes for a date. Never schedule on dates not listed above.
2. Prioritise subjects with nearer exams and weak subjects (average below target).
3. Use the exact subject names above. "topic" must be one of that subject's pending topics, or ""
   for general revision / practice tasks.
4. Give each task a short, specific, actionable title (e.g. "Practice integration by parts problems").
5. Tasks within a day must not overlap; use realistic start times between 07:00 and 21:00.
6. Each task's duration_mins must be between 15 and 120.
7. Spread topics across the period and leave revision of exam syllabi for the days just before exams.
"""


@dataclass
class _Context:
    prefs: StudyPreference
    subjects: list[Subject]
    plan_dates: list[date]
    available: dict[date, int]
    kept_tasks: list[StudyTask]
    replaceable_count: int


def _weekday(d: date) -> str:
    return VALID_DAYS[d.weekday()]


def _replaceable_filter(user: User, start: date, end: date) -> tuple:
    """Previous AI tasks that a new plan for this range may replace: pending, AI-generated, in range."""
    return (
        StudyTask.user_id == user.id,
        StudyTask.source == "ai",
        StudyTask.status == "pending",
        StudyTask.scheduled_date >= start,
        StudyTask.scheduled_date <= end,
    )


def _load_context(db: Session, user: User, start: date, end: date) -> _Context:
    prefs = preference_service.get_or_create(db, user)
    study_days = set(prefs.study_days.split(","))
    plan_dates = [
        d for i in range((end - start).days + 1)
        if _weekday(d := start + timedelta(days=i)) in study_days
    ]
    subjects = list(db.scalars(
        select(Subject).where(Subject.user_id == user.id)
        .options(selectinload(Subject.topics)).order_by(Subject.name)
    ))
    in_range = db.scalars(
        select(StudyTask).where(
            StudyTask.user_id == user.id,
            StudyTask.scheduled_date >= start,
            StudyTask.scheduled_date <= end,
        ).order_by(StudyTask.scheduled_date, StudyTask.start_time)
    ).all()
    # Manual and completed tasks stay; pending AI tasks will be replaced.
    kept = [t for t in in_range if not (t.source == "ai" and t.status == "pending")]
    used: dict[date, int] = {}
    for t in kept:
        used[t.scheduled_date] = used.get(t.scheduled_date, 0) + t.duration_mins
    available = {d: max(prefs.daily_study_minutes - used.get(d, 0), 0) for d in plan_dates}
    return _Context(
        prefs=prefs,
        subjects=subjects,
        plan_dates=plan_dates,
        available=available,
        kept_tasks=kept,
        replaceable_count=len(in_range) - len(kept),
    )


def build_prompt(db: Session, user: User, ctx: _Context, start: date, end: date) -> str:
    def lines(items: list[str], empty: str) -> str:
        return "\n".join(f"- {i}" for i in items) if items else f"- {empty}"

    subjects = [
        f"{s.name} (target {s.target_score}%): "
        + (", ".join(t.name for t in s.topics if t.status == "pending") or "no pending topics - revision only")
        for s in ctx.subjects
    ]
    today = user_today(user)
    names = {s.id: s.name for s in ctx.subjects}
    exams = [
        f"{e.exam_date.isoformat()} ({(e.exam_date - today).days} days away): {e.title}"
        + (f" [subject: {names[e.subject_id]}]" if e.subject_id in names else "")
        + (f" - syllabus: {e.syllabus}" if e.syllabus else "")
        for e in list_exams(db, user, upcoming=True)
    ]
    performance = [
        f"{p.subject}: "
        + (f"{p.avg_percentage}% vs target {p.target_score}%"
           + (" (WEAK - needs more time)" if p.avg_percentage < p.target_score else "")
           if p.avg_percentage is not None else f"no marks yet, target {p.target_score}%")
        for p in subject_performance(db, user)
    ]
    existing = [
        f"{t.scheduled_date.isoformat()} {t.start_time.strftime('%H:%M') if t.start_time else 'any time'}"
        f" for {t.duration_mins} min: {t.title}"
        for t in ctx.kept_tasks
    ]
    availability = [f"{d.isoformat()} ({_weekday(d)}): {ctx.available[d]} min" for d in ctx.plan_dates]
    return PROMPT_TEMPLATE.format(
        start=start.isoformat(),
        end=end.isoformat(),
        today=today.isoformat(),
        study_days=ctx.prefs.study_days,
        daily=ctx.prefs.daily_study_minutes,
        availability=lines(availability, "none"),
        goal=ctx.prefs.goal_note.strip() or "Not specified",
        subjects=lines(subjects, "none"),
        exams=lines(exams, "none"),
        performance=lines(performance, "none"),
        existing=lines(existing, "nothing"),
    )


def _parse_plan(text: str) -> AIPlan:
    cleaned = text.strip()
    if cleaned.startswith("```"):  # tolerate fenced output despite instructions
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    return AIPlan.model_validate(json.loads(cleaned))


def _request_plan(prompt: str) -> AIPlan:
    """Ask Gemini for a plan; retry once if the answer isn't valid JSON in the expected shape."""
    last_error: Exception | None = None
    for attempt in (1, 2):
        try:
            text = gemini_service.generate_json(prompt)
        except gemini_service.AIRateLimitError as exc:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, exc.message) from exc
        except gemini_service.AINotConfiguredError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, exc.message) from exc
        except gemini_service.AIError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, exc.message) from exc
        try:
            return _parse_plan(text)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Invalid AI plan on attempt %d: %s", attempt, exc)
            last_error = exc
    raise HTTPException(
        status.HTTP_502_BAD_GATEWAY,
        "The AI returned a plan we couldn't understand, even after retrying. Please try again.",
    ) from last_error


def _map_plan(plan: AIPlan, ctx: _Context) -> tuple[list[PlanDayPreview], list[SkippedItem]]:
    by_name = {s.name.strip().lower(): s for s in ctx.subjects}
    remaining = dict(ctx.available)
    tasks_by_date: dict[date, list[PlanTaskPreview]] = {d: [] for d in ctx.plan_dates}
    skipped: list[SkippedItem] = []

    for day in sorted(plan.days, key=lambda d: d.date):
        for task in sorted(day.tasks, key=lambda t: t.start_time):
            def skip(reason: str) -> None:
                skipped.append(SkippedItem(date=day.date.isoformat(), title=task.title, reason=reason))

            if day.date not in remaining:
                skip("Date is outside the plan range or not one of your study days")
                continue
            subject = by_name.get(task.subject.strip().lower())
            if subject is None:
                skip(f"Unknown subject '{task.subject}'")
                continue
            topic = None
            if task.topic and task.topic.strip():
                topic = next(
                    (t for t in subject.topics if t.name.strip().lower() == task.topic.strip().lower()),
                    None,
                )
                if topic is None:
                    skip(f"Unknown topic '{task.topic}' for {subject.name}")
                    continue
            if task.duration_mins > remaining[day.date]:
                skip("Would exceed your daily study minutes")
                continue
            remaining[day.date] -= task.duration_mins
            tasks_by_date[day.date].append(PlanTaskPreview(
                subject_id=subject.id,
                subject_name=subject.name,
                subject_color=subject.color,
                topic_id=topic.id if topic else None,
                topic_name=topic.name if topic else None,
                title=task.title.strip(),
                start_time=task.start_time,
                duration_mins=task.duration_mins,
            ))

    days = [
        PlanDayPreview(
            date=d,
            tasks=tasks,
            total_mins=sum(t.duration_mins for t in tasks),
            available_mins=ctx.available[d],
        )
        for d, tasks in tasks_by_date.items()
    ]
    return days, skipped


def generate_preview(db: Session, user: User, data: GeneratePlanRequest) -> PlanPreview:
    ctx = _load_context(db, user, data.start_date, data.end_date)
    if not ctx.subjects:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Add at least one subject before generating a plan.")
    if not any(ctx.available.values()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "There is no free study time in this date range. Check your study days and daily minutes.",
        )
    prompt = build_prompt(db, user, ctx, data.start_date, data.end_date)
    days, skipped = _map_plan(_request_plan(prompt), ctx)
    return PlanPreview(
        start_date=data.start_date,
        end_date=data.end_date,
        daily_study_minutes=ctx.prefs.daily_study_minutes,
        study_days=ctx.prefs.study_days,
        days=days,
        skipped=skipped,
        replaces_pending_ai_tasks=ctx.replaceable_count,
    )


def _validate_for_save(data: SavePlanRequest, ctx: _Context) -> list[tuple[date, PlanTaskIn]]:
    """Re-check a client-supplied plan: ownership, range, study days and daily minutes."""
    subjects = {s.id: s for s in ctx.subjects}
    remaining = dict(ctx.available)
    accepted: list[tuple[date, PlanTaskIn]] = []
    for day in data.days:
        if day.date not in remaining:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"{day.date.isoformat()} is outside the plan range or not one of your study days.",
            )
        for task in day.tasks:
            subject = subjects.get(task.subject_id)
            if subject is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")
            if task.topic_id is not None and task.topic_id not in {t.id for t in subject.topics}:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")
            remaining[day.date] -= task.duration_mins
            if remaining[day.date] < 0:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Tasks on {day.date.isoformat()} exceed your daily study minutes.",
                )
            accepted.append((day.date, task))
    return accepted


def save_plan(db: Session, user: User, data: SavePlanRequest) -> SavePlanResponse:
    ctx = _load_context(db, user, data.start_date, data.end_date)
    accepted = _validate_for_save(data, ctx)

    replace_filter = _replaceable_filter(user, data.start_date, data.end_date)
    replaced = db.scalar(select(func.count()).select_from(StudyTask).where(*replace_filter)) or 0
    db.execute(delete(StudyTask).where(*replace_filter))

    plan = StudyPlan(
        user_id=user.id,
        start_date=data.start_date,
        end_date=data.end_date,
        raw_json=data.model_dump(mode="json"),
    )
    db.add(plan)
    db.flush()
    db.add_all(
        StudyTask(
            user_id=user.id,
            subject_id=task.subject_id,
            topic_id=task.topic_id,
            title=task.title,
            scheduled_date=day,
            start_time=task.start_time,
            duration_mins=task.duration_mins,
            status="pending",
            source="ai",
            plan_id=plan.id,
        )
        for day, task in accepted
    )
    db.commit()
    return SavePlanResponse(plan_id=plan.id, tasks_created=len(accepted), tasks_replaced=replaced)
