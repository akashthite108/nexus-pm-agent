# NexusPM — Intelligent Project Management Agent

**NexusPM** is an AI-driven project planning and dynamic re-scheduling application built with **FastAPI**, **SQLite**, and a modern interactive web dashboard. It automates task breakdown, skill-based resource allocation, critical-path scheduling, and real-time schedule updates when requirements, timelines, or team availability change.

---

## Key Capabilities

* **Task Decomposition:** Breaks high-level project requirements into structured, sequential subtasks (`T1`, `T2`, ...) with explicit dependency mapping (`dependsOn`).
* **Chained Planning Pipeline:** Executes a deterministic multi-stage flow:
  1. **Decompose** requirements into a subtask dependency graph (DAG).
  2. **Allocate** team members based on required skills and estimate durations.
  3. **Schedule** exact start/end dates and detect critical-path deadline buffers or slips.
* **ReAct Dynamic Schedule Controller:** Handles mid-project disruptions (scope additions, task removals, weather/site delays, or team leave) using a transparent **`Thought → Action → Observation`** loop that modifies only affected downstream tasks.
* **Persistent SQLite Memory:** Stores project baselines, active schedules, and immutable change/decision audit logs in `nexus_pm_memory.db`.
* **Interactive Dashboard & Voice Walkthrough:** Includes a live Gantt timeline, task rationale inspector, team utilization tracker, and guided voice-narrated demos across real estate construction, civil procurement, statutory approvals, and software delivery.

---

## Project Structure

```text
nexus-pm-agent/
├── server.py           # FastAPI backend, DAG scheduler, ReAct controller & SQLite memory
├── index.html          # Interactive SaaS dashboard, Gantt chart & voice demo engine
├── requirements.txt    # Python dependencies
├── .gitignore          # Excludes venv, cache, and local .db files
└── README.md           # Project documentation
