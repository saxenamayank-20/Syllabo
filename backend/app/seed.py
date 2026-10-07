"""Create (or reset) a demo user with sample data. Run: python -m app.seed"""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Exam, Mark, StudyPreference, StudyTask, Subject, Topic, User

DEMO_EMAIL = "demo@syllabo.app"
DEMO_PASSWORD = "demo1234"
DEMO_TIMEZONE = "Asia/Kolkata"

SUBJECTS: list[tuple[str, str, int, list[str]]] = [
    ("Mathematics", "#2563eb", 80, ["Algebra", "Trigonometry", "Calculus", "Probability", "Matrices"]),
    ("Physics", "#ef4444", 80, ["Kinematics", "Laws of Motion", "Work & Energy", "Optics"]),
    ("Chemistry", "#f59e0b", 75, ["Atomic Structure", "Chemical Bonding", "Thermodynamics", "Organic Basics"]),
    ("Biology", "#10b981", 75, ["Cell Biology", "Photosynthesis", "Genetics", "Human Physiology"]),
    ("English", "#8b5cf6", 70, ["Comprehension", "Grammar", "Essay Writing"]),
]

# (subject, assessment, score, max_score, days_ago)
MARKS: list[tuple[str, str, float, float, int]] = [
    ("Mathematics", "Unit Test 1", 42, 50, 40), ("Mathematics", "Quiz 2", 18, 20, 12),
    ("Physics", "Unit Test 1", 34, 50, 38), ("Physics", "Quiz 2", 15, 20, 10),
    ("Chemistry", "Unit Test 1", 39, 50, 35), ("Chemistry", "Quiz 2", 16, 20, 9),
    ("Biology", "Unit Test 1", 44, 50, 33), ("Biology", "Quiz 2", 18, 20, 8),
    ("English", "Unit Test 1", 33, 50, 30), ("English", "Quiz 2", 15, 20, 7),
]

# (subject, title, start, duration, topic, completed, day_offset)
TASKS: list[tuple[str, str, time, int, str | None, bool, int]] = [
    ("Mathematics", "Read Chapter 3 - Algebra", time(9, 0), 60, "Algebra", True, 0),
    ("Biology", "Revise Photosynthesis Notes", time(10, 30), 45, "Photosynthesis", True, 0),
    ("Chemistry", "Watch Lecture - Chemical Bonding", time(12, 0), 60, "Chemical Bonding", False, 0),
    ("Physics", "Solve Previous Year Questions", time(14, 0), 60, None, False, 0),
    ("English", "Make Short Notes", time(16, 0), 30, None, False, 0),
    ("Mathematics", "Practice Trigonometry Problems", time(9, 0), 60, "Trigonometry", False, 1),
    ("Physics", "Revise Laws of Motion", time(11, 0), 45, "Laws of Motion", False, 1),
    ("Chemistry", "Thermodynamics Worksheet", time(15, 0), 60, "Thermodynamics", False, 2),
]


def seed() -> None:
    today = datetime.now(ZoneInfo(DEMO_TIMEZONE)).date()
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if existing:
            db.delete(existing)  # cascades to all of the demo user's data
            db.commit()

        user = User(
            name="Aarav Sharma", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
            email_verified=True, timezone=DEMO_TIMEZONE,
        )
        db.add(user)
        db.flush()

        db.add(StudyPreference(
            user_id=user.id, daily_study_minutes=180, study_days="Mon,Tue,Wed,Thu,Fri,Sat",
            goal_note="Score 85%+ in the finals, focus on Physics.",
        ))

        subjects: dict[str, Subject] = {}
        topics: dict[str, Topic] = {}
        for name, color, target, topic_names in SUBJECTS:
            subject = Subject(user_id=user.id, name=name, color=color, target_score=target)
            for i, topic_name in enumerate(topic_names):
                # Complete roughly the first half; a couple of them within the last week
                done = i < len(topic_names) // 2 + (1 if name == "Biology" else 0)
                completed_at = now - timedelta(days=2 if i == 0 else 14 + i) if done else None
                topic = Topic(
                    name=topic_name, status="completed" if done else "pending", completed_at=completed_at
                )
                subject.topics.append(topic)
                topics[topic_name] = topic
            db.add(subject)
            subjects[name] = subject
        db.flush()

        db.add_all([
            Exam(user_id=user.id, subject_id=subjects["Mathematics"].id, title="Mathematics - Unit Test",
                 syllabus="Chapter 1 - 5", exam_date=today + timedelta(days=12)),
            Exam(user_id=user.id, subject_id=subjects["Physics"].id, title="Science - Mid Term",
                 syllabus="Full Syllabus", exam_date=today + timedelta(days=19)),
            Exam(user_id=user.id, subject_id=subjects["English"].id, title="English - Test",
                 syllabus="Comprehension & Writing", exam_date=today + timedelta(days=26)),
            Exam(user_id=user.id, subject_id=subjects["Chemistry"].id, title="Chemistry - Quiz",
                 syllabus="Atomic Structure", exam_date=today - timedelta(days=5)),
        ])

        for subj, title, start, duration, topic_name, done, offset in TASKS:
            db.add(StudyTask(
                user_id=user.id, subject_id=subjects[subj].id,
                topic_id=topics[topic_name].id if topic_name else None,
                title=title, scheduled_date=today + timedelta(days=offset), start_time=start,
                duration_mins=duration, status="completed" if done else "pending", source="manual",
            ))

        for subj, name, score, max_score, days_ago in MARKS:
            db.add(Mark(
                user_id=user.id, subject_id=subjects[subj].id, assessment_name=name,
                score=score, max_score=max_score, assessment_date=today - timedelta(days=days_ago),
            ))

        db.commit()
    print(f"Seeded demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
