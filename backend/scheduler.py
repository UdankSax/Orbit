from datetime import (
    date,
    datetime,
    time,
    timedelta,
)

from sqlalchemy.orm import Session

from models import (
    Activity,
    Schedule,
    Subject,
    Task,
    Timetable,
)


DAY_NAMES = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]


SCHEDULE_START = time(8, 0)
SCHEDULE_END = time(23, 0)

# Tutorial preparation
PRACTICE_MINUTES = 45

# Normal self-study session size
SELF_STUDY_SESSION_MINUTES = 60

# Orbit doesn't try to fill the entire day.
DAILY_SELF_STUDY_LIMIT = 180


# ---------------------------------------------------------
# BASIC TIME HELPERS
# ---------------------------------------------------------

def to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def from_minutes(value: int) -> time:
    return time(
        value // 60,
        value % 60
    )


def overlaps(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:

    return (
        start_a < end_b
        and end_a > start_b
    )


def weekday_name(target_date: date) -> str:
    return DAY_NAMES[target_date.weekday()]


# ---------------------------------------------------------
# WEEK HELPERS
# ---------------------------------------------------------

def week_start(target_date: date) -> date:
    return target_date - timedelta(
        days=target_date.weekday()
    )


def week_end(target_date: date) -> date:
    return week_start(target_date) + timedelta(days=6)


# ---------------------------------------------------------
# BUSY TIME
# ---------------------------------------------------------

def get_busy_intervals(
    db: Session,
    target_date: date,
):
    """
    Returns all time blocks that Orbit is NOT allowed
    to schedule over.
    """

    busy = []

    day_name = weekday_name(target_date)

    # ---------------------------------------------
    # College timetable
    # ---------------------------------------------

    timetable = (
        db.query(Timetable)
        .filter(
            Timetable.day.ilike(day_name)
        )
        .all()
    )

    for item in timetable:

        busy.append(
            (
                to_minutes(item.start_time),
                to_minutes(item.end_time),
                "COLLEGE"
            )
        )

    # ---------------------------------------------
    # Personal activities
    # ---------------------------------------------

    activities = (
        db.query(Activity)
        .filter(
            Activity.day.ilike(day_name)
        )
        .all()
    )

    for item in activities:

        busy.append(
            (
                to_minutes(item.start_time),
                to_minutes(item.end_time),
                "ACTIVITY"
            )
        )

    # ---------------------------------------------
    # Fixed tasks
    # ---------------------------------------------

    fixed_tasks = (
        db.query(Task)
        .filter(
            Task.is_fixed == True,
            Task.status.notin_(
                ["COMPLETED", "CANCELLED"]
            )
        )
        .all()
    )

    for task in fixed_tasks:

        if (
            task.fixed_start_time is None
            or task.fixed_end_time is None
        ):
            continue

        busy.append(
            (
                to_minutes(task.fixed_start_time),
                to_minutes(task.fixed_end_time),
                "FIXED_TASK"
            )
        )

    # ---------------------------------------------
    # Existing generated schedule
    # ---------------------------------------------

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.date == target_date
        )
        .all()
    )

    for item in schedules:

        busy.append(
            (
                to_minutes(item.start_time),
                to_minutes(item.end_time),
                "SCHEDULE"
            )
        )

    busy.sort(key=lambda x: x[0])

    return busy


# ---------------------------------------------------------
# FREE TIME
# ---------------------------------------------------------

def get_free_intervals(
    db: Session,
    target_date: date,
):
    busy = get_busy_intervals(
        db,
        target_date
    )

    free = []

    cursor = to_minutes(SCHEDULE_START)

    for start, end, _ in busy:

        start = max(
            start,
            to_minutes(SCHEDULE_START)
        )

        end = min(
            end,
            to_minutes(SCHEDULE_END)
        )

        if end <= to_minutes(SCHEDULE_START):
            continue

        if start > cursor:

            free.append(
                (
                    cursor,
                    start
                )
            )

        cursor = max(
            cursor,
            end
        )

    if cursor < to_minutes(SCHEDULE_END):

        free.append(
            (
                cursor,
                to_minutes(SCHEDULE_END)
            )
        )

    return free


# ---------------------------------------------------------
# FIND A FREE SLOT
# ---------------------------------------------------------

def find_latest_slot_before(
    db: Session,
    target_date: date,
    deadline_minutes: int,
    required_minutes: int,
):
    """
    Finds the latest possible slot BEFORE a tutorial.

    Example:

    Tutorial:
    14:45

    Free:
    12:40 - 14:45

    Result:
    14:00 - 14:45
    """

    free = get_free_intervals(
        db,
        target_date
    )

    for start, end in reversed(free):

        end = min(
            end,
            deadline_minutes
        )

        if end <= start:
            continue

        if end - start >= required_minutes:

            return (
                end - required_minutes,
                end
            )

    return None


def find_first_slot(
    db: Session,
    target_date: date,
    required_minutes: int,
):
    free = get_free_intervals(
        db,
        target_date
    )

    for start, end in free:

        if end - start >= required_minutes:

            return (
                start,
                start + required_minutes
            )

    return None


# ---------------------------------------------------------
# SUBJECT STUDY PROGRESS
# ---------------------------------------------------------

def get_subject_study_minutes(
    db: Session,
    subject_id: int,
    start_date: date,
    end_date: date,
):
    """
    Counts SELF_STUDY sessions already scheduled
    for this subject during the current week.
    """

    schedules = (
        db.query(Schedule)
        .join(
            Task,
            Schedule.task_id == Task.id
        )
        .filter(
            Schedule.date >= start_date,
            Schedule.date <= end_date,
            Task.subject_id == subject_id,
            Task.task_type == "SELF_STUDY",
            Task.status != "CANCELLED",
        )
        .all()
    )

    total = 0

    for schedule in schedules:

        duration = (
            datetime.combine(
                date.today(),
                schedule.end_time
            )
            -
            datetime.combine(
                date.today(),
                schedule.start_time
            )
        ).seconds // 60

        total += duration

    return total


# ---------------------------------------------------------
# CREATE AUTO TASK
# ---------------------------------------------------------

def create_auto_task(
    db: Session,
    *,
    title: str,
    subject_id: int | None,
    task_type: str,
    estimated_minutes: int,
    deadline: datetime,
    priority: int = 8,
):
    task = Task(
        title=title,
        description="Automatically generated by Orbit.",
        estimated_minutes=estimated_minutes,
        deadline=deadline,
        priority=priority,
        status="SCHEDULED",
        task_type=task_type,
        subject_id=subject_id,
        is_fixed=False,
    )

    db.add(task)
    db.flush()

    return task


# ---------------------------------------------------------
# TUTORIAL PRACTICE
# ---------------------------------------------------------

def schedule_tutorial_practice(
    db: Session,
    target_date: date,
):
    """
    For every tutorial on the selected day:

        Tutorial
            ↓
        Practice before tutorial

    Orbit prefers the LATEST available slot immediately
    before the tutorial.
    """

    day_name = weekday_name(target_date)

    tutorials = (
        db.query(Timetable)
        .filter(
            Timetable.day.ilike(day_name)
        )
        .all()
    )

    tutorials = [
        item
        for item in tutorials
        if (
            "tutorial" in item.class_type.lower()
            or item.class_type.lower() in {
                "tut",
                "tut.",
            }
        )
    ]

    tutorials.sort(
        key=lambda x: to_minutes(x.start_time)
    )

    created = []

    for tutorial in tutorials:

        subject = (
            db.query(Subject)
            .filter(
                Subject.id == tutorial.subject_id
            )
            .first()
        )

        if subject is None:
            continue

        tutorial_start = to_minutes(
            tutorial.start_time
        )

        title = (
            f"Practice: {subject.name} "
            f"before tutorial"
        )

        # Prevent duplicate automatic sessions.
        existing = (
            db.query(Task)
            .filter(
                Task.title == title,
                Task.subject_id == subject.id,
                Task.task_type == "PRACTICE",
                Task.deadline >= datetime.combine(
                    target_date,
                    time.min
                ),
                Task.deadline <
                datetime.combine(
                    target_date + timedelta(days=1),
                    time.min
                ),
            )
            .first()
        )

        if existing:
            continue

        slot = find_latest_slot_before(
            db,
            target_date,
            tutorial_start,
            PRACTICE_MINUTES
        )

        if slot is None:
            continue

        start_minutes, end_minutes = slot

        task = create_auto_task(
            db,
            title=title,
            subject_id=subject.id,
            task_type="PRACTICE",
            estimated_minutes=PRACTICE_MINUTES,
            deadline=datetime.combine(
                target_date,
                tutorial.start_time
            ),
            priority=10,
        )

        schedule = Schedule(
            task_id=task.id,
            date=target_date,
            start_time=from_minutes(start_minutes),
            end_time=from_minutes(end_minutes),
            status="SCHEDULED",
        )

        db.add(schedule)

        created.append(task)

    db.commit()

    return created


# ---------------------------------------------------------
# SUBJECT SELF STUDY
# ---------------------------------------------------------

def schedule_subject_self_study(
    db: Session,
    target_date: date,
):
    """
    Allocates independent study time to subjects that
    are behind their weekly targets.

    Orbit:

    1. Looks at weekly target.
    2. Calculates already scheduled self-study.
    3. Finds the subjects with the largest deficit.
    4. Allocates 60-minute sessions.
    5. Limits automatic study to 3 hours/day.
    6. Gives each subject at most one generated
       session per day.
    """

    subjects = (
        db.query(Subject)
        .order_by(
            Subject.name
        )
        .all()
    )

    if not subjects:
        return []

    start_of_week = week_start(
        target_date
    )

    end_of_week = week_end(
        target_date
    )

    # Don't consume the entire day with auto study.
    daily_allocated = 0

    created = []

    subject_data = []

    for subject in subjects:

        target = (
            subject.self_study_target_minutes
            or 120
        )

        completed = get_subject_study_minutes(
            db,
            subject.id,
            start_of_week,
            end_of_week
        )

        deficit = max(
            0,
            target - completed
        )

        if deficit <= 0:
            continue

        # Check if Orbit already generated a self-study
        # session for this subject today.
        today_session = (
            db.query(Schedule)
            .join(
                Task,
                Schedule.task_id == Task.id
            )
            .filter(
                Schedule.date == target_date,
                Task.subject_id == subject.id,
                Task.task_type == "SELF_STUDY",
                Task.status != "CANCELLED",
            )
            .first()
        )

        if today_session:
            continue

        subject_data.append(
            {
                "subject": subject,
                "deficit": deficit,
                "target": target,
            }
        )

    # Highest deficit first.
    subject_data.sort(
        key=lambda item: item["deficit"],
        reverse=True
    )

    for item in subject_data:

        if daily_allocated >= DAILY_SELF_STUDY_LIMIT:
            break

        subject = item["subject"]
        deficit = item["deficit"]

        duration = min(
            SELF_STUDY_SESSION_MINUTES,
            deficit,
            DAILY_SELF_STUDY_LIMIT - daily_allocated
        )

        if duration < 30:
            continue

        slot = find_first_slot(
            db,
            target_date,
            duration
        )

        if slot is None:
            continue

        start_minutes, end_minutes = slot

        task = create_auto_task(
            db,
            title=f"Self Study: {subject.name}",
            subject_id=subject.id,
            task_type="SELF_STUDY",
            estimated_minutes=duration,
            deadline=datetime.combine(
                end_of_week,
                time(23, 59)
            ),
            priority=7,
        )

        schedule = Schedule(
            task_id=task.id,
            date=target_date,
            start_time=from_minutes(start_minutes),
            end_time=from_minutes(end_minutes),
            status="SCHEDULED",
        )

        db.add(schedule)

        created.append(task)

        daily_allocated += duration

        db.flush()

    db.commit()

    return created


# ---------------------------------------------------------
# NORMAL TASK SCHEDULING
# ---------------------------------------------------------

def schedule_normal_tasks(
    db: Session,
    target_date: date,
):
    """
    Schedules user-created pending tasks after
    tutorial preparation and subject study have
    been considered.
    """

    tasks = (
        db.query(Task)
        .filter(
            Task.status == "PENDING",
            Task.is_fixed == False,
            Task.task_type == "GENERAL",
        )
        .order_by(
            Task.deadline.asc(),
            Task.priority.desc(),
        )
        .all()
    )

    created = []

    for task in tasks:

        if task.deadline.date() < target_date:
            continue

        duration = task.estimated_minutes

        slot = find_first_slot(
            db,
            target_date,
            duration
        )

        if slot is None:
            continue

        start_minutes, end_minutes = slot

        schedule = Schedule(
            task_id=task.id,
            date=target_date,
            start_time=from_minutes(start_minutes),
            end_time=from_minutes(end_minutes),
            status="SCHEDULED",
        )

        db.add(schedule)

        task.status = "SCHEDULED"

        created.append(task)

        db.flush()

    db.commit()

    return created


# ---------------------------------------------------------
# MAIN ORBIT ENGINE
# ---------------------------------------------------------

def allocate_tasks(
    db: Session,
    target_date: date,
):
    """
    Main Orbit scheduling pipeline.

    Priority:

    1. Existing schedule
    2. Fixed college timetable
    3. Fixed personal activities
    4. Tutorial preparation
    5. Subject self-study
    6. User-created tasks

    This means Orbit doesn't simply fill empty spaces.
    It understands WHY a free period should be used.
    """

    # -------------------------------------------------
    # 1. Tutorial preparation
    # -------------------------------------------------

    practice_tasks = schedule_tutorial_practice(
        db,
        target_date
    )

    # -------------------------------------------------
    # 2. Subject self study
    # -------------------------------------------------

    self_study_tasks = schedule_subject_self_study(
        db,
        target_date
    )

    # -------------------------------------------------
    # 3. Normal tasks
    # -------------------------------------------------

    normal_tasks = schedule_normal_tasks(
        db,
        target_date
    )

    return {
        "practice": practice_tasks,
        "self_study": self_study_tasks,
        "normal": normal_tasks,
    }