const API = "http://127.0.0.1:8000";


// ============================================================
// STATE
// ============================================================

const realToday = new Date();

realToday.setHours(
    0,
    0,
    0,
    0
);

let selectedDate = new Date(
    realToday
);

let goals = [];
let tasks = [];
let activities = [];
let timetable = [];
let subjects = [];
let schedules = [];


// ============================================================
// DOM
// ============================================================

const goalForm =
    document.getElementById(
        "goalForm"
    );

const taskForm =
    document.getElementById(
        "taskForm"
    );

const activityForm =
    document.getElementById(
        "activityForm"
    );

const generateScheduleBtn =
    document.getElementById(
        "generateScheduleBtn"
    );

const previousDayBtn =
    document.getElementById(
        "previousDayBtn"
    );

const nextDayBtn =
    document.getElementById(
        "nextDayBtn"
    );

const todayBtn =
    document.getElementById(
        "todayBtn"
    );

const scheduleContainer =
    document.getElementById(
        "scheduleContainer"
    );

const goalsContainer =
    document.getElementById(
        "goalsContainer"
    );

const tasksContainer =
    document.getElementById(
        "tasksContainer"
    );

const activitiesContainer =
    document.getElementById(
        "activitiesContainer"
    );

const taskGoal =
    document.getElementById(
        "taskGoal"
    );

const toast =
    document.getElementById(
        "toast"
    );


// ============================================================
// HELPERS
// ============================================================

async function api(
    endpoint,
    options = {}
) {
    const response = await fetch(
        `${API}${endpoint}`,
        {
            headers: {
                "Content-Type":
                    "application/json"
            },
            ...options
        }
    );

    if (!response.ok) {
        let message =
            `HTTP ${response.status}`;

        try {
            const data =
                await response.json();

            message =
                data.detail ||
                message;
        } catch {}

        throw new Error(message);
    }

    return response.json();
}


function showToast(message) {

    if (!toast) return;

    toast.textContent =
        message;

    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove(
            "show"
        );
    }, 3000);
}


function formatDateForAPI(date) {

    const year =
        date.getFullYear();

    const month =
        String(
            date.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            date.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


function getDayName(date) {

    return [
        "SUNDAY",
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY"
    ][date.getDay()];
}


function isToday(date) {

    return (
        date.getFullYear() ===
            realToday.getFullYear() &&
        date.getMonth() ===
            realToday.getMonth() &&
        date.getDate() ===
            realToday.getDate()
    );
}


function formatReadableDate(date) {

    return date.toLocaleDateString(
        "en-US",
        {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric"
        }
    );
}


function minutesFromTime(time) {

    if (!time) return 0;

    const parts =
        time.substring(0, 5)
            .split(":");

    return (
        Number(parts[0]) * 60
        + Number(parts[1])
    );
}


function timeFromMinutes(minutes) {

    const hours =
        Math.floor(
            minutes / 60
        );

    const mins =
        minutes % 60;

    return (
        String(hours).padStart(2, "0")
        + ":"
        + String(mins).padStart(2, "0")
    );
}


function formatTime(time) {

    if (!time) return "";

    const [hour, minute] =
        time
            .substring(0, 5)
            .split(":")
            .map(Number);

    const suffix =
        hour >= 12
            ? "PM"
            : "AM";

    const displayHour =
        hour % 12 || 12;

    return `${displayHour}:${String(
        minute
    ).padStart(2, "0")} ${suffix}`;
}


function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// DATE UI
// ============================================================

function updateDateDisplay() {

    const label =
        document.getElementById(
            "selectedDateLabel"
        );

    if (!label) return;

    if (isToday(selectedDate)) {

        label.textContent =
            "Today · " +
            formatReadableDate(
                selectedDate
            );

    } else {

        label.textContent =
            formatReadableDate(
                selectedDate
            );
    }

    if (todayBtn) {
        todayBtn.style.opacity =
            isToday(selectedDate)
                ? "0.45"
                : "1";
    }
}


// ============================================================
// LOAD GOALS
// ============================================================

async function loadGoals() {

    try {

        goals =
            await api("/goals");

        renderGoals();

        populateGoalSelect();

        updateSummary();

    } catch (error) {

        console.error(error);

        goals = [];

        renderGoals();

        populateGoalSelect();
    }
}


// ============================================================
// GOAL RENDER
// ============================================================

function renderGoals() {

    if (!goalsContainer) return;

    if (!goals.length) {

        goalsContainer.innerHTML = `
            <div class="empty-state">
                No goals yet. Add your first goal below.
            </div>
        `;

        return;
    }

    goalsContainer.innerHTML =
        goals.map(goal => {

            const targetHours =
                goal.weekly_target_minutes
                / 60;

            const completedMinutes =
                getGoalCompletedMinutes(
                    goal.id
                );

            const completedHours =
                completedMinutes / 60;

            const percentage =
                goal.weekly_target_minutes > 0
                    ? Math.min(
                        100,
                        (
                            completedMinutes /
                            goal.weekly_target_minutes
                        ) * 100
                    )
                    : 0;

            return `
                <div class="goal-card">

                    <div class="goal-top">

                        <div class="goal-name">
                            ${escapeHTML(
                                goal.name
                            )}
                        </div>

                        <div class="goal-priority">
                            Priority ${goal.priority}/10
                        </div>

                    </div>

                    ${
                        goal.description
                            ? `
                                <div class="goal-description">
                                    ${escapeHTML(
                                        goal.description
                                    )}
                                </div>
                            `
                            : ""
                    }

                    <div class="goal-progress">

                        <div class="progress-bar">

                            <div
                                class="progress-fill"
                                style="
                                    width: ${percentage}%;
                                "
                            ></div>

                        </div>

                        <div class="goal-progress-info">

                            <span>
                                ${completedHours.toFixed(1)}h
                                / ${targetHours.toFixed(1)}h
                            </span>

                            <span>
                                ${Math.round(
                                    percentage
                                )}%
                            </span>

                        </div>

                    </div>

                </div>
            `;

        }).join("");
}


// ============================================================
// GOAL SELECT
// ============================================================

function populateGoalSelect() {

    if (!taskGoal) return;

    const currentValue =
        taskGoal.value;

    taskGoal.innerHTML = `
        <option value="">
            No goal
        </option>
    `;

    goals.forEach(goal => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            goal.id;

        option.textContent =
            goal.name;

        taskGoal.appendChild(
            option
        );
    });

    if (currentValue) {
        taskGoal.value =
            currentValue;
    }
}


// ============================================================
// LOAD TASKS
// ============================================================

async function loadTasks() {

    try {

        tasks =
            await api("/tasks");

        renderTasks();

        updateSummary();

        renderGoals();

    } catch (error) {

        console.error(error);

        tasks = [];

        renderTasks();
    }
}


// ============================================================
// TASK RENDER
// ============================================================

function renderTasks() {

    if (!tasksContainer) return;

    if (!tasks.length) {

        tasksContainer.innerHTML = `
            <div class="empty-state">
                No tasks yet.
            </div>
        `;

        return;
    }

    const sorted =
        [...tasks].sort(
            (a, b) =>
                new Date(a.deadline)
                -
                new Date(b.deadline)
        );

    tasksContainer.innerHTML =
        sorted.map(task => {

            return `
                <div class="task-item">

                    <div class="task-main">

                        <div>

                            <div class="task-title">
                                ${escapeHTML(
                                    task.title
                                )}
                            </div>

                            <div class="task-meta">
                                ${task.estimated_minutes} min
                                · Priority ${task.priority}
                                · ${escapeHTML(
                                    task.status
                                )}
                            </div>

                            ${
                                task.goal_name
                                    ? `
                                        <div class="goal-tag">
                                            ${escapeHTML(
                                                task.goal_name
                                            )}
                                        </div>
                                    `
                                    : ""
                            }

                        </div>

                        <div class="task-meta">
                            ${formatDeadline(
                                task.deadline
                            )}
                        </div>

                    </div>

                </div>
            `;

        }).join("");
}


function formatDeadline(deadline) {

    if (!deadline) return "";

    const date =
        new Date(deadline);

    return date.toLocaleDateString(
        "en-US",
        {
            month: "short",
            day: "numeric"
        }
    );
}


// ============================================================
// LOAD ACTIVITIES
// ============================================================

async function loadActivities() {

    try {

        activities =
            await api("/activities");

        renderActivities();

        updateSummary();

    } catch (error) {

        console.error(error);

        activities = [];

        renderActivities();
    }
}


// ============================================================
// ACTIVITY RENDER
// ============================================================

function renderActivities() {

    if (!activitiesContainer) return;

    const dayName =
        getDayName(selectedDate);

    const dayActivities =
        activities
            .filter(
                activity =>
                    activity.day ===
                    dayName
            )
            .sort(
                (a, b) =>
                    minutesFromTime(
                        a.start_time
                    )
                    -
                    minutesFromTime(
                        b.start_time
                    )
            );

    if (!dayActivities.length) {

        activitiesContainer.innerHTML = `
            <div class="empty-state">
                No activities on ${dayName}.
            </div>
        `;

        return;
    }

    activitiesContainer.innerHTML =
        dayActivities.map(
            activity => {

                return `
                    <div class="activity-item">

                        <div class="activity-main">

                            <div>

                                <div class="activity-title">
                                    ${escapeHTML(
                                        activity.title
                                    )}
                                </div>

                                <div class="activity-meta">
                                    ${formatTime(
                                        activity.start_time
                                    )}
                                    →
                                    ${formatTime(
                                        activity.end_time
                                    )}
                                </div>

                            </div>

                            <div class="activity-meta">
                                ${activity.day}
                            </div>

                        </div>

                    </div>
                `;

            }
        ).join("");
}


// ============================================================
// LOAD TIMETABLE
// ============================================================

async function loadTimetable() {

    try {

        timetable =
            await api("/timetable");

        subjects =
            await api("/subjects");

    } catch (error) {

        console.error(error);

        timetable = [];
        subjects = [];
    }
}


// ============================================================
// LOAD SCHEDULE
// ============================================================

async function loadSchedule() {

    try {

        schedules =
            await api(
                `/schedule?target_date=${formatDateForAPI(
                    selectedDate
                )}`
            );

        renderDailyTimeline();

        updateSummary();

    } catch (error) {

        console.error(error);

        schedules = [];

        renderDailyTimeline();
    }
}


// ============================================================
// GOAL PROGRESS
// ============================================================

function getGoalCompletedMinutes(
    goalId
) {

    let total = 0;

    schedules.forEach(schedule => {

        if (
            Number(schedule.goal_id) ===
            Number(goalId)
        ) {

            total +=
                minutesFromTime(
                    schedule.end_time
                )
                -
                minutesFromTime(
                    schedule.start_time
                );
        }
    });

    return total;
}


// ============================================================
// SUBJECT LOOKUP
// ============================================================

function getSubjectName(
    subjectId
) {

    const subject =
        subjects.find(
            item =>
                Number(item.id) ===
                Number(subjectId)
        );

    return subject
        ? subject.name
        : "College";
}


// ============================================================
// ORBIT SCHEDULE TITLE
// ============================================================

function getScheduleTitle(
    schedule
) {

    /*
     * New backend response:
     *
     * task_title
     * task_type
     * subject_name
     * goal_name
     *
     * The old frontend was incorrectly using:
     *
     * schedule.title
     *
     * which does not exist in the new API.
     */

    if (schedule.task_title) {
        return schedule.task_title;
    }

    if (
        schedule.task_type ===
        "SELF_STUDY"
    ) {

        return schedule.subject_name
            ? `Self Study: ${schedule.subject_name}`
            : "Self Study";
    }

    if (
        schedule.task_type ===
        "PRACTICE"
    ) {

        return schedule.subject_name
            ? `Practice: ${schedule.subject_name}`
            : "Tutorial Practice";
    }

    if (schedule.goal_name) {
        return schedule.goal_name;
    }

    return "Orbit Session";
}


function getScheduleMeta(
    schedule
) {

    if (
        schedule.task_type ===
        "PRACTICE"
    ) {

        return schedule.subject_name
            ? `Practice · ${schedule.subject_name}`
            : "Tutorial Practice";
    }

    if (
        schedule.task_type ===
        "SELF_STUDY"
    ) {

        return schedule.subject_name
            ? `Self Study · ${schedule.subject_name}`
            : "Self Study";
    }

    if (schedule.goal_name) {
        return `Task · ${schedule.goal_name}`;
    }

    return "Orbit";
}


// ============================================================
// DAILY TIMELINE
// ============================================================

function renderDailyTimeline() {

    if (!scheduleContainer) return;

    const dayName =
        getDayName(selectedDate);

    const blocks = [];


    // --------------------------------------------------------
    // COLLEGE
    // --------------------------------------------------------

    timetable
        .filter(
            entry =>
                entry.day ===
                dayName
        )
        .forEach(entry => {

            blocks.push({
                type: "college",

                title:
                    getSubjectName(
                        entry.subject_id
                    ),

                meta:
                    entry.class_type
                    || "College",

                start:
                    entry.start_time,

                end:
                    entry.end_time
            });
        });


    // --------------------------------------------------------
    // ACTIVITIES
    // --------------------------------------------------------

    activities
        .filter(
            activity =>
                activity.day ===
                dayName
        )
        .forEach(activity => {

            blocks.push({
                type: "activity",

                title:
                    activity.title,

                meta:
                    "Activity",

                start:
                    activity.start_time,

                end:
                    activity.end_time
            });
        });


    // --------------------------------------------------------
    // ORBIT TASKS
    // --------------------------------------------------------

    schedules
        .forEach(schedule => {

            blocks.push({
                type: "orbit",

                /*
                 * FIX:
                 * Use task_title from the new backend.
                 */
                title:
                    getScheduleTitle(
                        schedule
                    ),

                /*
                 * Show what kind of Orbit session
                 * this actually is.
                 */
                meta:
                    getScheduleMeta(
                        schedule
                    ),

                start:
                    schedule.start_time,

                end:
                    schedule.end_time,

                taskType:
                    schedule.task_type,

                subjectName:
                    schedule.subject_name,

                goalName:
                    schedule.goal_name
            });
        });


    // --------------------------------------------------------
    // SORT OCCUPIED BLOCKS
    // --------------------------------------------------------

    blocks.sort(
        (a, b) =>
            minutesFromTime(a.start)
            -
            minutesFromTime(b.start)
    );


    // --------------------------------------------------------
    // ADD FREE TIME
    // --------------------------------------------------------

    const allBlocks =
        [];

    let current =
        8 * 60;


    blocks.forEach(block => {

        const start =
            minutesFromTime(
                block.start
            );

        const end =
            minutesFromTime(
                block.end
            );


        if (start > current) {

            allBlocks.push({
                type: "free",

                title: "Free Time",

                meta:
                    "Available for Orbit",

                start:
                    timeFromMinutes(
                        current
                    ),

                end:
                    timeFromMinutes(
                        start
                    )
            });
        }


        allBlocks.push(block);


        if (end > current) {
            current = end;
        }

    });


    if (current < 23 * 60) {

        allBlocks.push({

            type: "free",

            title: "Free Time",

            meta:
                "Available for Orbit",

            start:
                timeFromMinutes(
                    current
                ),

            end:
                "23:00"
        });
    }


    // --------------------------------------------------------
    // RENDER
    // --------------------------------------------------------

    if (!allBlocks.length) {

        scheduleContainer.innerHTML = `
            <div class="empty-state">
                No schedule information for this day.
            </div>
        `;

        return;
    }


    scheduleContainer.innerHTML =
        allBlocks.map(
            block => {

                const duration =
                    minutesFromTime(
                        block.end
                    )
                    -
                    minutesFromTime(
                        block.start
                    );

                return `
                    <div class="
                        timeline-item
                        ${block.type}
                    ">

                        <div class="timeline-time">

                            <strong>
                                ${formatTime(
                                    block.start
                                )}
                            </strong>

                            <span>
                                ${formatTime(
                                    block.end
                                )}
                            </span>

                        </div>


                        <div class="timeline-content">

                            <div class="timeline-title">
                                ${escapeHTML(
                                    block.title
                                )}
                            </div>

                            <div class="timeline-meta">
                                ${escapeHTML(
                                    block.meta
                                )}
                                · ${duration} min
                            </div>

                            ${
                                block.type === "orbit"
                                    ? `
                                        <span class="timeline-badge">
                                            ORBIT
                                        </span>
                                    `
                                    : ""
                            }

                        </div>

                    </div>
                `;

            }
        ).join("");
}


// ============================================================
// SUMMARY
// ============================================================

function updateSummary() {

    const goalCount =
        document.getElementById(
            "goalCount"
        );

    const taskCount =
        document.getElementById(
            "taskCount"
        );

    const scheduledCount =
        document.getElementById(
            "scheduledCount"
        );

    const activityCount =
        document.getElementById(
            "activityCount"
        );


    if (goalCount) {

        goalCount.textContent =
            goals.filter(
                goal =>
                    goal.status ===
                    "ACTIVE"
            ).length;
    }


    if (taskCount) {

        taskCount.textContent =
            tasks.length;
    }


    if (scheduledCount) {

        scheduledCount.textContent =
            schedules.length;
    }


    if (activityCount) {

        const dayName =
            getDayName(
                selectedDate
            );

        activityCount.textContent =
            activities.filter(
                activity =>
                    activity.day ===
                    dayName
            ).length;
    }
}


// ============================================================
// ADD GOAL
// ============================================================

if (goalForm) {

    goalForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            try {

                const name =
                    document.getElementById(
                        "goalName"
                    ).value.trim();

                const description =
                    document.getElementById(
                        "goalDescription"
                    ).value.trim();

                const hours =
                    Number(
                        document.getElementById(
                            "goalTarget"
                        ).value
                    );

                const priority =
                    Number(
                        document.getElementById(
                            "goalPriority"
                        ).value
                    );


                await api(
                    "/goals",
                    {
                        method: "POST",

                        body: JSON.stringify({

                            name,

                            description:
                                description
                                || null,

                            weekly_target_minutes:
                                Math.round(
                                    hours * 60
                                ),

                            priority,

                            status:
                                "ACTIVE"
                        })
                    }
                );


                goalForm.reset();

                document.getElementById(
                    "goalTarget"
                ).value = 5;

                document.getElementById(
                    "goalPriority"
                ).value = 5;


                await loadGoals();

                showToast(
                    "Goal added."
                );

            } catch (error) {

                console.error(error);

                showToast(
                    error.message
                );
            }
        }
    );
}


// ============================================================
// ADD TASK
// ============================================================

if (taskForm) {

    taskForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            try {

                const title =
                    document.getElementById(
                        "taskTitle"
                    ).value.trim();

                const description =
                    document.getElementById(
                        "taskDescription"
                    ).value.trim();

                const estimatedMinutes =
                    Number(
                        document.getElementById(
                            "taskMinutes"
                        ).value
                    );

                const priority =
                    Number(
                        document.getElementById(
                            "taskPriority"
                        ).value
                    );

                const deadline =
                    document.getElementById(
                        "taskDeadline"
                    ).value;

                const selectedGoal =
                    taskGoal.value;


                await api(
                    "/tasks",
                    {
                        method: "POST",

                        body: JSON.stringify({

                            title,

                            description:
                                description
                                || null,

                            estimated_minutes:
                                estimatedMinutes,

                            deadline:
                                new Date(
                                    deadline
                                ).toISOString(),

                            priority,

                            status:
                                "PENDING",

                            is_fixed:
                                false,

                            fixed_start_time:
                                null,

                            fixed_end_time:
                                null,

                            goal_id:
                                selectedGoal
                                    ? Number(
                                        selectedGoal
                                    )
                                    : null
                        })
                    }
                );


                taskForm.reset();

                document.getElementById(
                    "taskMinutes"
                ).value = 60;

                document.getElementById(
                    "taskPriority"
                ).value = 5;


                await loadTasks();

                showToast(
                    "Task added."
                );

            } catch (error) {

                console.error(error);

                showToast(
                    error.message
                );
            }
        }
    );
}


// ============================================================
// ADD ACTIVITY
// ============================================================

if (activityForm) {

    activityForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            try {

                const title =
                    document.getElementById(
                        "activityTitle"
                    ).value.trim();

                const day =
                    document.getElementById(
                        "activityDay"
                    ).value;

                const start =
                    document.getElementById(
                        "activityStart"
                    ).value;

                const end =
                    document.getElementById(
                        "activityEnd"
                    ).value;


                await api(
                    "/activities",
                    {
                        method: "POST",

                        body: JSON.stringify({

                            title,

                            day,

                            start_time:
                                start,

                            end_time:
                                end
                        })
                    }
                );


                activityForm.reset();

                await loadActivities();

                renderDailyTimeline();

                showToast(
                    "Activity added."
                );

            } catch (error) {

                console.error(error);

                showToast(
                    error.message
                );
            }
        }
    );
}


// ============================================================
// GENERATE SCHEDULE
// ============================================================

if (generateScheduleBtn) {

    generateScheduleBtn.addEventListener(
        "click",
        async () => {

            try {

                generateScheduleBtn.disabled =
                    true;

                generateScheduleBtn.textContent =
                    "Planning...";


                const date =
                    formatDateForAPI(
                        selectedDate
                    );


                const result =
                    await api(
                        `/schedule/generate?target_date=${date}`,
                        {
                            method: "POST"
                        }
                    );


                await Promise.all([
                    loadTasks(),
                    loadSchedule(),
                    loadGoals()
                ]);


                const practice =
                    result.practice_sessions || 0;

                const selfStudy =
                    result.self_study_sessions || 0;

                const normal =
                    result.normal_tasks || 0;

                const total =
                    practice +
                    selfStudy +
                    normal;


                if (total > 0) {

                    showToast(
                        `Orbit created ${total} session${
                            total === 1
                                ? ""
                                : "s"
                        }.`
                    );

                } else {

                    showToast(
                        "No new sessions were created."
                    );
                }

            } catch (error) {

                console.error(error);

                showToast(
                    error.message
                );

            } finally {

                generateScheduleBtn.disabled =
                    false;

                generateScheduleBtn.textContent =
                    "Generate Schedule";
            }
        }
    );
}


// ============================================================
// DATE NAVIGATION
// ============================================================

if (previousDayBtn) {

    previousDayBtn.addEventListener(
        "click",
        async () => {

            selectedDate.setDate(
                selectedDate.getDate() - 1
            );

            await refreshSelectedDate();
        }
    );
}


if (nextDayBtn) {

    nextDayBtn.addEventListener(
        "click",
        async () => {

            selectedDate.setDate(
                selectedDate.getDate() + 1
            );

            await refreshSelectedDate();
        }
    );
}


if (todayBtn) {

    todayBtn.addEventListener(
        "click",
        async () => {

            selectedDate =
                new Date(realToday);

            await refreshSelectedDate();
        }
    );
}


// ============================================================
// REFRESH DATE
// ============================================================

async function refreshSelectedDate() {

    updateDateDisplay();

    await Promise.all([
        loadSchedule(),
        loadActivities()
    ]);

    renderDailyTimeline();

    updateSummary();
}


// ============================================================
// INITIAL LOAD
// ============================================================

async function initialize() {

    updateDateDisplay();

    try {

        await Promise.all([
            loadGoals(),
            loadTasks(),
            loadActivities(),
            loadTimetable(),
            loadSchedule()
        ]);

        renderDailyTimeline();

        updateSummary();

    } catch (error) {

        console.error(error);

        showToast(
            "Could not connect to Orbit backend."
        );
    }
}


initialize();