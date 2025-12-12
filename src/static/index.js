/**
 * FastAPI + Celery Demo - Client-side JavaScript
 * Manages task creation, tracking, and worker monitoring
 */

/**
 * @typedef {Object} Task
 * @property {string} state - Current task state (PENDING, STARTED, SUCCESS, FAILURE, REVOKED)
 * @property {number} progress - Task progress percentage (0-100)
 * @property {string} [date_done] - ISO timestamp of task completion
 */

/**
 * @typedef {Object} Worker
 * @property {string} worker_name - Full worker name including hostname
 * @property {number} max_concurrency - Maximum concurrent tasks
 * @property {number} uptime - Worker uptime in seconds
 * @property {string[]} registered_tasks - List of task names registered with this worker
 */

/**
 * @typedef {Object} AppConfig
 * @property {string[]} terminal_states - List of terminal task states
 */

/** @type {Map<string, Task>} Map of task IDs to task data */
const tasks = new Map();

/** @type {AppConfig|null} Application configuration from server */
let appConfig = null;

/** @type {string|null} Task ID waiting for verification after creation */
let pendingTaskId = null;

/** @type {number|null} Timeout ID for form re-enable safety mechanism */
let formDisabledTimeout = null;

/** @constant {number} How often to refresh workers list (milliseconds) */
const WORKERS_REFRESH_INTERVAL = 30000; // 30 seconds

/** @constant {number} How often to refresh tasks list (milliseconds) */
const TASKS_REFRESH_INTERVAL = 5000; // 5 seconds

/** @constant {number} Maximum time to wait for task verification (milliseconds) */
const FORM_ENABLE_TIMEOUT = 10000; // 10 seconds

/**
 * Disables the task creation form to prevent duplicate submissions
 * Shows spinner in the form header to indicate processing
 */
function disableTaskForm() {
    const durationInput = document.getElementById('duration');
    const submitButton = document.querySelector('#taskForm button[type="submit"]');
    const formElement = document.getElementById('taskForm');
    const taskFormSpinner = document.getElementById('taskFormSpinner');

    if (durationInput) durationInput.disabled = true;
    if (submitButton) submitButton.disabled = true;
    if (formElement) formElement.style.cursor = 'wait';
    if (taskFormSpinner) taskFormSpinner.style.display = 'inline-block';
}

/**
 * Re-enables the task creation form after task creation completes
 * Hides spinner and clears any pending state
 */
function enableTaskForm() {
    const durationInput = document.getElementById('duration');
    const submitButton = document.querySelector('#taskForm button[type="submit"]');
    const formElement = document.getElementById('taskForm');
    const taskFormSpinner = document.getElementById('taskFormSpinner');

    if (durationInput) durationInput.disabled = false;
    if (submitButton) submitButton.disabled = false;
    if (formElement) formElement.style.cursor = '';
    if (taskFormSpinner) taskFormSpinner.style.display = 'none';

    // Clear pending state
    pendingTaskId = null;
    if (formDisabledTimeout) {
        clearTimeout(formDisabledTimeout);
        formDisabledTimeout = null;
    }
}

/**
 * Loads application configuration from the server
 * Configuration includes terminal states and other app settings
 * @async
 */
async function loadAppConfig() {
    try {
        const response = await fetch('/config');
        if (response.ok) {
            appConfig = await response.json();
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

/**
 * Formats uptime in seconds to human-readable string
 * @param {number} uptimeSeconds - Uptime in seconds
 * @returns {string} Formatted uptime string
 * @example
 * formatUptime(90) // "1 minute 30 seconds"
 * formatUptime(3661) // "1 hour 1 minute"
 * formatUptime(86401) // "1 day"
 */
function formatUptime(uptimeSeconds) {
    const days = Math.floor(uptimeSeconds / 86400);
    const hours = Math.floor((uptimeSeconds % 86400) / 3600);
    const minutes = Math.floor((uptimeSeconds % 3600) / 60);
    const seconds = uptimeSeconds % 60;

    if (days >= 1) {
        return `${days} day${days !== 1 ? 's' : ''}`;
    } else if (hours >= 1) {
        return `${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`;
    } else if (minutes >= 1) {
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ${seconds} second${seconds !== 1 ? 's' : ''}`;
    } else {
        return `${seconds} second${seconds !== 1 ? 's' : ''}`;
    }
}

/**
 * Displays workers in the workers table
 * Shows "No workers available" message if worker list is empty
 * @param {Worker[]} workers - Array of worker objects from the API
 */
function displayWorkersTable(workers) {
    const workersList = document.getElementById('workersList');

    if (workers.length === 0) {
        workersList.innerHTML = `
            <tr class="table-danger">
                <td colspan="4" class="text-center text-danger">No workers available</td>
            </tr>
        `;
        return;
    }

    workersList.innerHTML = workers.map(worker => {
        const uptimeStr = formatUptime(worker.uptime);

        // Format registered tasks as HTML line breaks
        const registeredTasksHtml = worker.registered_tasks && worker.registered_tasks.length > 0
            ? worker.registered_tasks.join('<br />')
            : '<span class="text-muted">None</span>';

        return `
            <tr>
                <td>${worker.worker_name}</td>
                <td>${worker.max_concurrency}</td>
                <td>${uptimeStr}</td>
                <td>${registeredTasksHtml}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Fetches and updates the workers list from the API
 * Shows spinner during loading and updates the workers table
 * @async
 */
async function updateWorkersCount() {
    try {
        const workersSpinner = document.getElementById('workersSpinner');

        // Show spinner while loading
        if (workersSpinner) {
            workersSpinner.style.display = 'inline-block';
        }

        const response = await fetch('/workers');
        if (response.ok) {
            const workers = await response.json();
            displayWorkersTable(workers);
        }
    } catch (error) {
        console.error('Error loading workers:', error);
    } finally {
        // Hide spinner after loading
        const workersSpinner = document.getElementById('workersSpinner');
        if (workersSpinner) {
            workersSpinner.style.display = 'none';
        }
    }
}

/**
 * Refreshes the tasks table by fetching current tasks from the API
 * Shows "No tasks" message if task list is empty
 * Handles pending task verification after task creation
 * @async
 */
async function refreshTasks() {
    try {
        const taskSpinner = document.getElementById('taskSpinner');

        // Show spinner while loading
        if (taskSpinner) {
            taskSpinner.style.display = 'inline-block';
        }

        const response = await fetch('/tasks');
        if (response.ok) {
            const taskData = await response.json();

            // Check if pending task appears in the list BEFORE clearing DOM
            if (pendingTaskId) {
                const taskExists = taskData.some(task => task.task_id === pendingTaskId);
                if (taskExists) {
                    // Task verified! Re-enable form
                    enableTaskForm();
                }
            }

            // Clear existing rows
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';

            // Show "No tasks" message if empty
            if (taskData.length === 0) {
                taskList.innerHTML = `
                    <tr class="table-secondary">
                        <td colspan="5" class="text-center text-muted">No tasks</td>
                    </tr>
                `;
            } else {
                taskData.forEach(task => {
                    displayTask(
                        task.task_id,
                        task.state,
                        task.date_done,
                        task.name,
                        false,  // prepend
                        task.progress  // progress
                    );
                });
            }
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    } finally {
        // Hide spinner after loading
        const taskSpinner = document.getElementById('taskSpinner');
        if (taskSpinner) {
            taskSpinner.style.display = 'none';
        }
    }
}

/**
 * Generates HTML for the progress/completed column
 * Shows progress bar for STARTED state with known progress
 * Shows spinner for STARTED state with unknown progress
 * Shows completion time for completed tasks
 * @param {number|null} progress - Task progress (0-100) or null if unknown
 * @param {string} state - Current task state
 * @param {string|null} dateDone - ISO timestamp of task completion
 * @returns {string} HTML string for the progress/completed cell
 */
function getProgressOrCompletedHtml(progress, state, dateDone) {
    // Show progress bar or spinner for STARTED state
    if (state === 'STARTED') {
        // If progress is known, show progress bar
        if (progress !== null && progress !== undefined) {
            const progressPercent = Math.round(progress);

            return `
                <div class="progress" style="min-width: 100px;">
                    <div class="progress-bar"
                         role="progressbar"
                         style="width: ${progressPercent}%"
                         aria-valuenow="${progressPercent}"
                         aria-valuemin="0"
                         aria-valuemax="100">
                        ${progressPercent}%
                    </div>
                </div>
            `;
        } else {
            // If progress is unknown, show small spinner
            return `
                <span class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </span>
            `;
        }
    }

    // Show completion date if available
    if (dateDone) {
        return new Date(dateDone).toLocaleTimeString();
    }

    // Otherwise show hyphen
    return '-';
}

/**
 * Displays a task row in the tasks table
 * Applies appropriate styling based on task state
 * @param {string} taskId - Unique task identifier
 * @param {string} state - Current task state (PENDING, STARTED, SUCCESS, FAILURE, REVOKED)
 * @param {string|null} dateDone - ISO timestamp of task completion
 * @param {string|null} name - Task name/description
 * @param {boolean} prepend - If true, insert at top of table; otherwise append to bottom
 * @param {number|null} progress - Task progress percentage (0-100)
 */
function displayTask(taskId, state, dateDone, name = null, prepend = false, progress = null) {
    const taskRow = document.createElement('tr');
    taskRow.id = `task-${taskId}`;

    // Determine background color based on state
    const bgClasses = {
        'PENDING': 'table-warning',
        'STARTED': 'table-info',
        'SUCCESS': 'table-success',
        'FAILURE': 'table-danger',
        'REVOKED': 'table-secondary'
    };
    const bgClass = bgClasses[state] || 'table-secondary';
    taskRow.className = bgClass;

    // Determine button text based on state (use config)
    const buttonText = appConfig && appConfig.terminal_states.includes(state) ? 'Delete' : 'Cancel';

    const nameText = name || '-';
    const progressOrCompletedHtml = getProgressOrCompletedHtml(progress, state, dateDone);

    taskRow.innerHTML = `
        <td>${taskId}</td>
        <td><span id="name-${taskId}">${nameText}</span></td>
        <td><span id="status-${taskId}">${state}</span></td>
        <td><div id="progress-completed-${taskId}">${progressOrCompletedHtml}</div></td>
        <td>
            <button class="btn btn-danger btn-sm" onclick="deleteTask('${taskId}')">
                ${buttonText}
            </button>
        </td>
    `;

    const taskList = document.getElementById('taskList');
    if (prepend) {
        taskList.insertBefore(taskRow, taskList.firstChild);
    } else {
        taskList.appendChild(taskRow);
    }
    tasks.set(taskId, { state, progress: progress || 0 });
}

/**
 * Updates an existing task's status in the UI
 * Updates state, progress, styling, and button text
 * @param {string} taskId - Unique task identifier
 * @param {string} state - New task state
 * @param {string|null} dateDone - ISO timestamp of task completion
 * @param {number|null} progress - Task progress percentage (0-100)
 */
function updateTaskStatus(taskId, state, dateDone, progress = null) {
    const statusSpan = document.getElementById(`status-${taskId}`);
    const taskRow = document.getElementById(`task-${taskId}`);
    const progressCompletedDiv = document.getElementById(`progress-completed-${taskId}`);

    if (statusSpan) {
        statusSpan.textContent = state;
    }

    // Update progress/completed column
    if (progressCompletedDiv) {
        progressCompletedDiv.innerHTML = getProgressOrCompletedHtml(progress, state, dateDone);
    }

    if (taskRow) {
        // Bootstrap table-* utilities for row coloring
        const bgClasses = {
            'PENDING': 'table-warning',
            'STARTED': 'table-info',
            'SUCCESS': 'table-success',
            'FAILURE': 'table-danger',
            'REVOKED': 'table-secondary'
        };
        const bgClass = bgClasses[state] || 'table-secondary';
        taskRow.className = bgClass;

        // Update button text when task reaches terminal state
        const button = taskRow.querySelector('button');
        if (button && appConfig && appConfig.terminal_states.includes(state)) {
            button.textContent = 'Delete';
        }
    }

    const task = tasks.get(taskId);
    if (task) {
        task.state = state;
        task.progress = progress || 0;
        if (dateDone) {
            task.date_done = dateDone;
        }
    }
}

/**
 * Deletes or cancels a task
 * For terminal state tasks: removes from table and local state
 * For active tasks: updates state to REVOKED
 * @async
 * @param {string} taskId - Unique task identifier to delete
 */
async function deleteTask(taskId) {
    const taskSpinner = document.getElementById('taskSpinner');

    try {
        // Show spinner while deleting
        if (taskSpinner) {
            taskSpinner.style.display = 'inline-block';
        }

        await fetch(`/tasks/${taskId}`, { method: 'DELETE' });

        const task = tasks.get(taskId);
        const currentState = task?.state;

        if (appConfig && appConfig.terminal_states.includes(currentState)) {
            // For terminal state tasks, remove from table
            const taskRow = document.getElementById(`task-${taskId}`);
            if (taskRow) {
                taskRow.remove();
            }
            tasks.delete(taskId);
        } else {
            // For active tasks, update to REVOKED
            updateTaskStatus(taskId, 'REVOKED');
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        alert('Failed to delete task');
    } finally {
        // Hide spinner after deletion
        if (taskSpinner) {
            taskSpinner.style.display = 'none';
        }
    }
}

/**
 * Task form submission handler
 * Creates a new sleep task and waits for verification
 * Disables form until task appears in the tasks list
 */
document.getElementById('taskForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const duration = parseInt(document.getElementById('duration').value);

    // Disable form and show wait cursor
    disableTaskForm();

    try {
        const response = await fetch('/tasks/sleep_task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration })
        });

        if (response.ok) {
            const data = await response.json();

            // Store pending task ID for verification
            pendingTaskId = data.task_id;

            // Don't display task immediately - wait for refresh to pick it up
            // This prevents DOM manipulation from interfering with form state

            // Set safety timeout to re-enable form after 10 seconds
            formDisabledTimeout = setTimeout(() => {
                console.warn('Form re-enabled after timeout - task may not have appeared');
                enableTaskForm();
            }, FORM_ENABLE_TIMEOUT);

            // Form will be re-enabled when task appears in refreshTasks()
        } else {
            // Handle non-ok response
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || 'Failed to create task';
            alert(errorMessage);
            enableTaskForm();
        }
    } catch (error) {
        console.error('Error creating task:', error);
        alert('Failed to create task: ' + error.message);
        enableTaskForm();
    }
});

/**
 * Application initialization on page load
 * Loads configuration, fetches initial data, and sets up refresh intervals
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Load config first since it's needed to determine button text
    await loadAppConfig();
    // Then load workers and tasks in parallel
    await Promise.all([updateWorkersCount(), refreshTasks()]);
    // Refresh workers count every 30 seconds
    setInterval(updateWorkersCount, WORKERS_REFRESH_INTERVAL);
    // Auto-refresh task list every 5 seconds
    setInterval(refreshTasks, TASKS_REFRESH_INTERVAL);
});
