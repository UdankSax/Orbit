from datetime import date

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Subject, Timetable, Activity, Task, Schedule
from schemas import ActivityCreate, TaskCreate
from scheduler import allocate_tasks


app = FastAPI()


# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Database
# -------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Root
# -------------------------

@app.get("/")
def root():
    return {
        "message": "Orbit is running"
    }


# -------------------------
# Subjects
# -------------------------

@app.get("/subjects")
def get_subjects(
    db: Session = Depends(get_db)
):
    return db.query(Subject).all()


# -------------------------
# Timetable
# -------------------------

@app.get("/timetable")
def get_timetable(
    db: Session = Depends(get_db)
):
    return db.query(Timetable).all()


# -------------------------
# Activities
# -------------------------

@app.get("/activities")
def get_activities(
    db: Session = Depends(get_db)
):
    return db.query(Activity).all()


@app.post("/activities")
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db)
):
    new_activity = Activity(
        title=activity.title,
        day=activity.day,
        start_time=activity.start_time,
        end_time=activity.end_time
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return new_activity


# -------------------------
# Tasks
# -------------------------

@app.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db)
):
    return db.query(Task).all()


@app.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    new_task = Task(
        title=task.title,
        description=task.description,
        estimated_minutes=task.estimated_minutes,
        deadline=task.deadline,
        priority=task.priority,
        status=task.status,
        is_fixed=task.is_fixed,
        fixed_start_time=task.fixed_start_time,
        fixed_end_time=task.fixed_end_time
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# -------------------------
# Schedule
# -------------------------

@app.get("/schedule")
def get_schedule(
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).order_by(
        Schedule.date,
        Schedule.start_time
    ).all()

    result = []

    for item in schedule:

        task = db.query(Task).filter(
            Task.id == item.task_id
        ).first()

        result.append({
            "id": item.id,
            "task_id": item.task_id,
            "title": task.title if task else "Unknown Task",
            "description": task.description if task else None,
            "date": item.date,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "status": item.status
        })

    return result


@app.post("/schedule/generate")
def generate_schedule(
    target_date: date,
    db: Session = Depends(get_db)
):
    allocations = allocate_tasks(
        db,
        target_date
    )

    return {
        "date": target_date,
        "scheduled_tasks": [
            {
                "title": title,
                "date": scheduled_date,
                "start_time": start,
                "end_time": end
            }
            for title, scheduled_date, start, end in allocations
        ]
    }