const API = "http://127.0.0.1:8000";


// ==================================================
// DATE
// ==================================================

const today = new Date();

const todayString =
    today.toISOString().split("T")[0];

const todayDay =
    today
        .toLocaleDateString(
            "en-US",
            { weekday: "long" }
        )
        .toUpperCase();


// ==================================================
// DISPLAY DATE
// ==================================================

document.getElementById("todayDate").textContent =
    today.toLocaleDateString(
        "en-US",
        {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric"
        }
    );


// ==================================================
// LOAD TASKS
// ==================================================

async function loadTasks() {

    try {

        const response =
            await fetch(`${API}/tasks`);

        if (!response.ok) {
            throw new Error("Failed to load tasks");
        }

        const tasks =
            await response.json();

        const container =
            document.getElementById(
                "tasksContainer"
            );

        document.getElementById(
            "taskCount"
        ).textContent = tasks.length;


        if (tasks.length === 0) {

            container.innerHTML =
                `<p class="empty">
                    No tasks yet.
                </p>`;

            return;
        }


        container.innerHTML =
            tasks.map(task => {

                return `
                    <div class="task">

                        <div class="task-title">
                            ${task.title}
                        </div>

                        <div class="task-meta">
                            ${task.estimated_minutes}
                            minutes
                            · Priority ${task.priority}
                            · ${task.status}
                        </div>

                    </div>
                `;

            }).join("");


    } catch (error) {

        console.error(error);

        document.getElementById(
            "tasksContainer"
        ).innerHTML =
            `<p class="empty">
                Could not load tasks.
            </p>`;
    }
}


// ==================================================
// LOAD ACTIVITIES
// ==================================================

async function loadActivities() {

    try {

        const response =
            await fetch(`${API}/activities`);

        if (!response.ok) {
            throw new Error(
                "Failed to load activities"
            );
        }

        const activities =
            await response.json();

        const container =
            document.getElementById(
                "activitiesContainer"
            );


        const todaysActivities =
            activities.filter(
                activity =>
                    activity.day === todayDay
            );


        document.getElementById(
            "activityCount"
        ).textContent =
            todaysActivities.length;


        if (todaysActivities.length === 0) {

            container.innerHTML =
                `<p class="empty">
                    No activities today.
                </p>`;

            return;
        }


        container.innerHTML =
            todaysActivities.map(activity => {

                return `
                    <div class="activity">

                        <strong>
                            ${activity.title}
                        </strong>

                        <span>
                            ${activity.start_time.slice(0, 5)}
                            -
                            ${activity.end_time.slice(0, 5)}
                        </span>

                    </div>
                `;

            }).join("");


    } catch (error) {

        console.error(error);

        document.getElementById(
            "activitiesContainer"
        ).innerHTML =
            `<p class="empty">
                Could not load activities.
            </p>`;
    }
}


// ==================================================
// LOAD SCHEDULE
// ==================================================

async function loadSchedule() {

    try {

        const response =
            await fetch(`${API}/schedule`);

        if (!response.ok) {
            throw new Error(
                "Failed to load schedule"
            );
        }

        const schedule =
            await response.json();

        const container =
            document.getElementById(
                "scheduleContainer"
            );


        const todaysSchedule =
            schedule.filter(
                item =>
                    item.date === todayString
            );


        document.getElementById(
            "scheduledCount"
        ).textContent =
            todaysSchedule.length;


        if (todaysSchedule.length === 0) {

            container.innerHTML =
                `<p class="empty">
                    No schedule generated for today.
                </p>`;

            return;
        }


        container.innerHTML =
            todaysSchedule.map(item => {

                return `
                    <div class="timeline-item">

                        <div class="timeline-time">
                            ${item.start_time.slice(0, 5)}
                            -
                            ${item.end_time.slice(0, 5)}
                        </div>

                        <div class="timeline-title">
                            ${item.title}
                        </div>

                    </div>
                `;

            }).join("");


    } catch (error) {

        console.error(error);

        document.getElementById(
            "scheduleContainer"
        ).innerHTML =
            `<p class="empty">
                Could not load schedule.
            </p>`;
    }
}


// ==================================================
// ADD TASK
// ==================================================

async function addTask(event) {

    event.preventDefault();


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

    const deadline =
        document.getElementById(
            "taskDeadline"
        ).value;

    const priority =
        Number(
            document.getElementById(
                "taskPriority"
            ).value
        );


    if (
        !title ||
        !estimatedMinutes ||
        !deadline
    ) {

        alert(
            "Please fill in all required fields."
        );

        return;
    }


    const task = {

        title: title,

        description:
            description || null,

        estimated_minutes:
            estimatedMinutes,

        deadline:
            new Date(deadline).toISOString(),

        priority:
            priority,

        status:
            "PENDING",

        is_fixed:
            false,

        fixed_start_time:
            null,

        fixed_end_time:
            null
    };


    try {

        const response =
            await fetch(
                `${API}/tasks`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(task)
                }
            );


        if (!response.ok) {

            const error =
                await response.text();

            console.error(error);

            throw new Error(
                "Could not create task"
            );
        }


        document.getElementById(
            "taskForm"
        ).reset();


        await loadTasks();

        alert(
            "Task added successfully."
        );


    } catch (error) {

        console.error(error);

        alert(
            "Could not add task."
        );
    }
}


// ==================================================
// ADD ACTIVITY
// ==================================================

async function addActivity(event) {

    event.preventDefault();


    const title =
        document.getElementById(
            "activityTitle"
        ).value.trim();

    const day =
        document.getElementById(
            "activityDay"
        ).value;

    const startTime =
        document.getElementById(
            "activityStart"
        ).value;

    const endTime =
        document.getElementById(
            "activityEnd"
        ).value;


    if (
        !title ||
        !startTime ||
        !endTime
    ) {

        alert(
            "Please fill in all required fields."
        );

        return;
    }


    if (startTime >= endTime) {

        alert(
            "End time must be after start time."
        );

        return;
    }


    const activity = {

        title:
            title,

        day:
            day,

        start_time:
            startTime + ":00",

        end_time:
            endTime + ":00"
    };


    try {

        const response =
            await fetch(
                `${API}/activities`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(activity)
                }
            );


        if (!response.ok) {

            const error =
                await response.text();

            console.error(error);

            throw new Error(
                "Could not create activity"
            );
        }


        document.getElementById(
            "activityForm"
        ).reset();


        await loadActivities();

        alert(
            "Activity added successfully."
        );


    } catch (error) {

        console.error(error);

        alert(
            "Could not add activity."
        );
    }
}


// ==================================================
// GENERATE SCHEDULE
// ==================================================

async function generateSchedule() {

    const button =
        document.getElementById(
            "generateBtn"
        );


    button.disabled = true;

    button.textContent =
        "Generating...";


    try {

        const response =
            await fetch(
                `${API}/schedule/generate?target_date=${todayString}`,
                {
                    method: "POST"
                }
            );


        if (!response.ok) {

            const error =
                await response.text();

            console.error(error);

            throw new Error(
                "Failed to generate schedule"
            );
        }


        await loadTasks();

        await loadSchedule();


    } catch (error) {

        console.error(error);

        alert(
            "Could not generate schedule."
        );


    } finally {

        button.disabled = false;

        button.textContent =
            "Generate Schedule";
    }
}


// ==================================================
// EVENT LISTENERS
// ==================================================

document
    .getElementById("taskForm")
    .addEventListener(
        "submit",
        addTask
    );


document
    .getElementById("activityForm")
    .addEventListener(
        "submit",
        addActivity
    );


document
    .getElementById("generateBtn")
    .addEventListener(
        "click",
        generateSchedule
    );


// ==================================================
// INITIAL LOAD
// ==================================================

loadTasks();

loadActivities();

loadSchedule();