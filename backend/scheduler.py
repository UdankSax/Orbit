from datetime import time, date

from database import SessionLocal
from models import Timetable, Activity, Task, Schedule


# --------------------------------------------------
# BLOCKED INTERVALS
# --------------------------------------------------

def get_blocked_intervals(timetable, activities, fixed_tasks):
    """
    Convert timetable entries, activities, and fixed tasks
    into blocked time intervals.
    """

    blocked = []

    for entry in timetable:
        blocked.append(
            (
                entry.start_time,
                entry.end_time
            )
        )

    for activity in activities:
        blocked.append(
            (
                activity.start_time,
                activity.end_time
            )
        )

    for task in fixed_tasks:
        if task.fixed_start_time and task.fixed_end_time:
            blocked.append(
                (
                    task.fixed_start_time,
                    task.fixed_end_time
                )
            )

    return blocked


# --------------------------------------------------
# FREE SLOTS
# --------------------------------------------------

def calculate_free_slots(
    blocked_intervals,
    day_start=time(8, 0),
    day_end=time(23, 0)
):
    """
    Calculate free time slots from blocked intervals.
    """

    blocked_intervals = sorted(
        blocked_intervals,
        key=lambda interval: interval[0]
    )

    free_slots = []

    current_time = day_start

    for start, end in blocked_intervals:

        if start > current_time:
            free_slots.append(
                (current_time, start)
            )

        if end > current_time:
            current_time = end

    if current_time < day_end:
        free_slots.append(
            (current_time, day_end)
        )

    return free_slots


# --------------------------------------------------
# TIME HELPERS
# --------------------------------------------------

def time_to_minutes(t):
    """
    Convert datetime.time into minutes from midnight.
    """

    return t.hour * 60 + t.minute


def minutes_to_time(minutes):
    """
    Convert minutes from midnight into datetime.time.
    """

    hours = minutes // 60
    mins = minutes % 60

    return time(hours, mins)


# --------------------------------------------------
# TASK ALLOCATION
# --------------------------------------------------

def allocate_tasks(db, target_date):
    """
    Allocate pending non-fixed tasks into available
    time slots for a specific date.

    V1 rules:
    - College timetable blocks time.
    - Activities block time.
    - Fixed tasks block time.
    - A task must fit completely inside one free slot.
    - A task is scheduled only once.
    - Successfully scheduled tasks become SCHEDULED.
    """

    day_name = target_date.strftime("%A").upper()

    # ----------------------------------------------
    # Load college timetable
    # ----------------------------------------------

    timetable = db.query(Timetable).filter(
        Timetable.day == day_name
    ).all()

    # ----------------------------------------------
    # Load activities
    # ----------------------------------------------

    activities = db.query(Activity).filter(
        Activity.day == day_name
    ).all()

    # ----------------------------------------------
    # Load fixed tasks
    # ----------------------------------------------

    fixed_tasks = db.query(Task).filter(
        Task.is_fixed == True,
        Task.fixed_start_time.isnot(None),
        Task.fixed_end_time.isnot(None)
    ).all()

    # ----------------------------------------------
    # Calculate blocked time
    # ----------------------------------------------

    blocked = get_blocked_intervals(
        timetable,
        activities,
        fixed_tasks
    )

    # ----------------------------------------------
    # Calculate free time
    # ----------------------------------------------

    free_slots = calculate_free_slots(blocked)

    # ----------------------------------------------
    # Find tasks already scheduled for this date
    # ----------------------------------------------

    existing_schedule = db.query(Schedule).filter(
        Schedule.date == target_date
    ).all()

    already_scheduled_task_ids = set()

    for schedule in existing_schedule:

        already_scheduled_task_ids.add(
            schedule.task_id
        )

        # Make sure the task status matches reality.
        task = db.query(Task).filter(
            Task.id == schedule.task_id
        ).first()

        if task and task.status == "PENDING":
            task.status = "SCHEDULED"

    # ----------------------------------------------
    # Get pending automatic tasks
    # ----------------------------------------------

    tasks = db.query(Task).filter(
        Task.status == "PENDING",
        Task.is_fixed == False,
        Task.id.notin_(already_scheduled_task_ids)
    ).order_by(
        Task.deadline.asc(),
        Task.priority.desc()
    ).all()

    # ----------------------------------------------
    # Allocate tasks
    # ----------------------------------------------

    allocations = []

    for task in tasks:

        required_minutes = task.estimated_minutes

        for index, (slot_start, slot_end) in enumerate(free_slots):

            slot_start_minutes = time_to_minutes(
                slot_start
            )

            slot_end_minutes = time_to_minutes(
                slot_end
            )

            available_minutes = (
                slot_end_minutes -
                slot_start_minutes
            )

            # --------------------------------------
            # Task fits
            # --------------------------------------

            if available_minutes >= required_minutes:

                task_start = slot_start

                task_end = minutes_to_time(
                    slot_start_minutes +
                    required_minutes
                )

                # Create schedule entry
                new_schedule = Schedule(
                    task_id=task.id,
                    date=target_date,
                    start_time=task_start,
                    end_time=task_end,
                    status="SCHEDULED"
                )

                db.add(new_schedule)

                # Update task status
                task.status = "SCHEDULED"

                allocations.append(
                    (
                        task.title,
                        target_date,
                        task_start,
                        task_end
                    )
                )

                # ----------------------------------
                # Shrink the free slot
                # ----------------------------------

                free_slots[index] = (
                    task_end,
                    slot_end
                )

                break

    # ----------------------------------------------
    # Save everything
    # ----------------------------------------------

    db.commit()

    return allocations


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    db = SessionLocal()

    try:

        target_date = date.today()

        print("\nGENERATING SCHEDULE FOR:")
        print(target_date)

        allocations = allocate_tasks(
            db,
            target_date
        )

        if not allocations:

            print(
                "\nNo new tasks were scheduled."
            )

        else:

            print(
                "\nNEWLY SCHEDULED TASKS:"
            )

            for (
                title,
                scheduled_date,
                start,
                end
            ) in allocations:

                print(
                    f"{title} | "
                    f"{scheduled_date} | "
                    f"{start} → {end}"
                )

    finally:
        db.close()