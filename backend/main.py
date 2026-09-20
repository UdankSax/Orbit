from datetime import date

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from database import SessionLocal

from models import (
    Subject,
    Timetable,
    Activity,
    Goal,
    Task,
    Schedule,
)

from schemas import (
    ActivityCreate,
    GoalCreate,
    TaskCreate,
)

from scheduler import allocate_tasks


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Orbit API",
    description="Adaptive personal scheduling engine",
    version="0.3.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "name": "Orbit",
        "status": "online",
        "version": "0.3.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# SUBJECTS
# =========================================================

@app.get("/subjects")
def get_subjects(
    db: Session = Depends(get_db)
):
    subjects = (
        db.query(Subject)
        .order_by(Subject.id)
        .all()
    )

    return [
        {
            "id": subject.id,
            "name": subject.name,
            "self_study_target_minutes": (
                subject.self_study_target_minutes
            ),
        }
        for subject in subjects
    ]


@app.patch("/subjects/{subject_id}/target")
def update_subject_target(
    subject_id: int,
    target_minutes: int,
    db: Session = Depends(get_db),
):
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id)
        .first()
    )

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail="Subject not found",
        )

    if target_minutes < 0:
        raise HTTPException(
            status_code=400,
            detail="Target cannot be negative",
        )

    subject.self_study_target_minutes = target_minutes

    db.commit()
    db.refresh(subject)

    return {
        "id": subject.id,
        "name": subject.name,
        "self_study_target_minutes": (
            subject.self_study_target_minutes
        ),
    }


# =========================================================
# TIMETABLE
# =========================================================

@app.get("/timetable")
def get_timetable(
    db: Session = Depends(get_db)
):
    rows = (
        db.query(
            Timetable,
            Subject
        )
        .join(
            Subject,
            Timetable.subject_id == Subject.id
        )
        .all()
    )

    return [
        {
            "id": timetable.id,
            "subject_id": timetable.subject_id,
            "subject": subject.name,
            "day": timetable.day,
            "start_time": timetable.start_time,
            "end_time": timetable.end_time,
            "class_type": timetable.class_type,
        }
        for timetable, subject in rows
    ]


# =========================================================
# ACTIVITIES
# =========================================================

@app.get("/activities")
def get_activities(
    db: Session = Depends(get_db)
):
    activities = (
        db.query(Activity)
        .order_by(
            Activity.day,
            Activity.start_time
        )
        .all()
    )

    return [
        {
            "id": activity.id,
            "title": activity.title,
            "day": activity.day,
            "start_time": activity.start_time,
            "end_time": activity.end_time,
        }
        for activity in activities
    ]


@app.post("/activities")
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
):
    if activity.start_time >= activity.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time",
        )

    new_activity = Activity(
        title=activity.title,
        day=activity.day.upper(),
        start_time=activity.start_time,
        end_time=activity.end_time,
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return {
        "id": new_activity.id,
        "title": new_activity.title,
        "day": new_activity.day,
        "start_time": new_activity.start_time,
        "end_time": new_activity.end_time,
    }


# =========================================================
# GOALS
# =========================================================

def get_goal_scheduled_minutes(
    db: Session,
    goal_id: int,
):
    """
    Calculate how many minutes are currently scheduled
    for a goal.
    """

    schedules = (
        db.query(Schedule)
        .join(
            Task,
            Schedule.task_id == Task.id
        )
        .filter(
            Task.goal_id == goal_id,
            Task.status != "CANCELLED",
        )
        .all()
    )

    total = 0

    for schedule in schedules:

        start = (
            schedule.start_time.hour * 60
            + schedule.start_time.minute
        )

        end = (
            schedule.end_time.hour * 60
            + schedule.end_time.minute
        )

        total += max(
            0,
            end - start
        )

    return total


@app.get("/goals")
def get_goals(
    db: Session = Depends(get_db)
):
    goals = (
        db.query(Goal)
        .filter(
            Goal.status == "ACTIVE"
        )
        .order_by(
            Goal.priority.desc()
        )
        .all()
    )

    result = []

    for goal in goals:

        scheduled_minutes = (
            get_goal_scheduled_minutes(
                db,
                goal.id,
            )
        )

        remaining = max(
            0,
            goal.weekly_target_minutes
            - scheduled_minutes
        )

        if goal.weekly_target_minutes > 0:
            pressure = (
                remaining
                / goal.weekly_target_minutes
            )
        else:
            pressure = 0

        result.append(
            {
                "id": goal.id,
                "name": goal.name,
                "description": goal.description,
                "weekly_target_minutes": (
                    goal.weekly_target_minutes
                ),
                "priority": goal.priority,
                "status": goal.status,

                "scheduled_minutes_this_week": (
                    scheduled_minutes
                ),

                "remaining_minutes": remaining,

                "pressure": pressure,
            }
        )

    return result


@app.post("/goals")
def create_goal(
    goal: GoalCreate,
    db: Session = Depends(get_db),
):
    if goal.weekly_target_minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="Weekly target must be greater than 0",
        )

    if not 1 <= goal.priority <= 10:
        raise HTTPException(
            status_code=400,
            detail="Priority must be between 1 and 10",
        )

    new_goal = Goal(
        name=goal.name,
        description=goal.description,
        weekly_target_minutes=(
            goal.weekly_target_minutes
        ),
        priority=goal.priority,
        status=goal.status,
    )

    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    return {
        "id": new_goal.id,
        "name": new_goal.name,
        "description": new_goal.description,
        "weekly_target_minutes": (
            new_goal.weekly_target_minutes
        ),
        "priority": new_goal.priority,
        "status": new_goal.status,
    }


# =========================================================
# TASKS
# =========================================================

@app.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db)
):
    tasks = (
        db.query(Task)
        .order_by(
            Task.deadline.asc(),
            Task.priority.desc(),
        )
        .all()
    )

    result = []

    for task in tasks:

        goal_name = None
        subject_name = None

        if task.goal_id is not None:

            goal = (
                db.query(Goal)
                .filter(
                    Goal.id == task.goal_id
                )
                .first()
            )

            if goal:
                goal_name = goal.name

        if task.subject_id is not None:

            subject = (
                db.query(Subject)
                .filter(
                    Subject.id == task.subject_id
                )
                .first()
            )

            if subject:
                subject_name = subject.name

        result.append(
            {
                "id": task.id,

                "goal_id": task.goal_id,
                "goal_name": goal_name,

                "subject_id": task.subject_id,
                "subject_name": subject_name,

                "title": task.title,
                "description": task.description,

                "estimated_minutes": (
                    task.estimated_minutes
                ),

                "deadline": task.deadline,

                "priority": task.priority,

                "status": task.status,

                "task_type": task.task_type,

                "is_fixed": task.is_fixed,

                "fixed_start_time": (
                    task.fixed_start_time
                ),

                "fixed_end_time": (
                    task.fixed_end_time
                ),
            }
        )

    return result


@app.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Basic validation
    # -----------------------------------------------------

    if task.estimated_minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="Estimated minutes must be greater than 0",
        )

    if not 1 <= task.priority <= 10:
        raise HTTPException(
            status_code=400,
            detail="Priority must be between 1 and 10",
        )

    if task.task_type not in {
        "GENERAL",
        "PRACTICE",
        "SELF_STUDY",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid task type",
        )

    # -----------------------------------------------------
    # Goal validation
    # -----------------------------------------------------

    if task.goal_id is not None:

        goal = (
            db.query(Goal)
            .filter(
                Goal.id == task.goal_id
            )
            .first()
        )

        if goal is None:
            raise HTTPException(
                status_code=404,
                detail="Goal not found",
            )

    # -----------------------------------------------------
    # Subject validation
    # -----------------------------------------------------

    if task.subject_id is not None:

        subject = (
            db.query(Subject)
            .filter(
                Subject.id == task.subject_id
            )
            .first()
        )

        if subject is None:
            raise HTTPException(
                status_code=404,
                detail="Subject not found",
            )

    # -----------------------------------------------------
    # Fixed task validation
    # -----------------------------------------------------

    if task.is_fixed:

        if (
            task.fixed_start_time is None
            or task.fixed_end_time is None
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Fixed tasks require "
                    "fixed_start_time and "
                    "fixed_end_time"
                ),
            )

        if (
            task.fixed_start_time
            >= task.fixed_end_time
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Fixed task start time "
                    "must be before end time"
                ),
            )

    # -----------------------------------------------------
    # Create task
    # -----------------------------------------------------

    new_task = Task(
        goal_id=task.goal_id,
        subject_id=task.subject_id,

        title=task.title,
        description=task.description,

        estimated_minutes=(
            task.estimated_minutes
        ),

        deadline=task.deadline,

        priority=task.priority,

        status=task.status,

        task_type=task.task_type,

        is_fixed=task.is_fixed,

        fixed_start_time=(
            task.fixed_start_time
        ),

        fixed_end_time=(
            task.fixed_end_time
        ),
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "id": new_task.id,

        "goal_id": new_task.goal_id,
        "subject_id": new_task.subject_id,

        "title": new_task.title,
        "description": new_task.description,

        "estimated_minutes": (
            new_task.estimated_minutes
        ),

        "deadline": new_task.deadline,

        "priority": new_task.priority,

        "status": new_task.status,

        "task_type": new_task.task_type,

        "is_fixed": new_task.is_fixed,

        "fixed_start_time": (
            new_task.fixed_start_time
        ),

        "fixed_end_time": (
            new_task.fixed_end_time
        ),
    }


# =========================================================
# SCHEDULE
# =========================================================

@app.get("/schedule")
def get_schedule(
    target_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Schedule,
            Task,
        )
        .join(
            Task,
            Schedule.task_id == Task.id
        )
    )

    if target_date is not None:

        query = query.filter(
            Schedule.date == target_date
        )

    query = query.order_by(
        Schedule.date,
        Schedule.start_time,
    )

    rows = query.all()

    result = []

    for schedule, task in rows:

        goal_name = None
        subject_name = None

        if task.goal_id is not None:

            goal = (
                db.query(Goal)
                .filter(
                    Goal.id == task.goal_id
                )
                .first()
            )

            if goal:
                goal_name = goal.name

        if task.subject_id is not None:

            subject = (
                db.query(Subject)
                .filter(
                    Subject.id == task.subject_id
                )
                .first()
            )

            if subject:
                subject_name = subject.name

        result.append(
            {
                "id": schedule.id,

                "task_id": schedule.task_id,

                "date": schedule.date,

                "start_time": schedule.start_time,

                "end_time": schedule.end_time,

                "status": schedule.status,

                "task_title": task.title,

                "task_type": task.task_type,

                "goal_id": task.goal_id,

                "goal_name": goal_name,

                "subject_id": task.subject_id,

                "subject_name": subject_name,
            }
        )

    return result


# =========================================================
# GENERATE ORBIT SCHEDULE
# =========================================================

@app.post("/schedule/generate")
def generate_schedule(
    target_date: date,
    db: Session = Depends(get_db),
):
    try:

        result = allocate_tasks(
            db,
            target_date,
        )

        return {
            "success": True,
            "date": target_date,

            "practice_sessions": len(
                result.get(
                    "practice",
                    []
                )
            ),

            "self_study_sessions": len(
                result.get(
                    "self_study",
                    []
                )
            ),

            "normal_tasks": len(
                result.get(
                    "normal",
                    []
                )
            ),
        }

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )