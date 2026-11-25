import re
import json
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="NexusPM Offline Agent (No API Key)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "nexus_pm_memory.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            start_date TEXT,
            deadline TEXT,
            requirements TEXT,
            team_json TEXT,
            tasks_json TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            timestamp TEXT,
            type TEXT,
            summary TEXT,
            trace TEXT
        )
    """)
    conn.commit()
    conn.close()


def seed_default_projects():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM projects")
    if c.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        demos = [
            {
                "id": "proj-real-estate-site",
                "name": "Tower A Construction & Site Work",
                "start": "2026-11-25",
                "deadline": "2026-12-10",
                "req": "Execute Tower A Floor 5 finishing: MEP electrical & plumbing conduit rough-in, internal & external wall plastering, waterproofing & curing, primer & final wall painting, and final site handover inspection.",
                "team": [
                    {"name": "Rajesh", "role": "MEP Engineer", "skills": ["Wiring", "Plumbing", "Conduits"]},
                    {"name": "Suresh", "role": "Civil Contractor", "skills": ["Plastering", "Waterproofing", "Masonry"]},
                    {"name": "Anita", "role": "Finishing & QA Lead", "skills": ["Painting", "Snag Inspection", "Handover"]},
                ],
                "tasks": [
                    {"id": "T1", "title": "MEP Electrical & Plumbing Conduit Rough-in", "assignee": "Rajesh", "dependsOn": [], "days": 3, "rationale": "Rajesh owns MEP conduits; must finish before walls are plastered.", "modified": False},
                    {"id": "T2", "title": "Internal & External Wall Plastering", "assignee": "Suresh", "dependsOn": ["T1"], "days": 4, "rationale": "Suresh handles plastering once T1 conduits are concealed.", "modified": False},
                    {"id": "T3", "title": "Waterproofing & Curing Check", "assignee": "Suresh", "dependsOn": ["T2"], "days": 2, "rationale": "Curing required after plastering before paint adhesion.", "modified": False},
                    {"id": "T4", "title": "Primer & Final Interior Painting", "assignee": "Anita", "dependsOn": ["T3"], "days": 3, "rationale": "Anita leads finishing & painting after plaster curing passes.", "modified": False},
                    {"id": "T5", "title": "Flat Snag List & Handover Inspection", "assignee": "Anita", "dependsOn": ["T4"], "days": 2, "rationale": "Final quality check before client possession.", "modified": False},
                ],
                "log_summary": "Decomposed Tower A site finishing into 5 sequential civil/MEP tasks (14-day critical path).",
                "log_trace": "Chain Step 1: Split requirements into 5 dependent tasks.\nChain Step 2: Matched Rajesh, Suresh, and Anita by trade.\nChain Step 3: Computed baseline dates.",
            },
            {
                "id": "proj-real-estate-proc",
                "name": "TMT Steel & Cement Procurement",
                "start": "2026-11-25",
                "deadline": "2026-12-07",
                "req": "Procure 50 tons of Fe-550D TMT steel and 800 bags of OPC-53 cement for Phase 2 slab casting: collect 3 vendor quotations, compare landed rates with GST, issue Purchase Order, track dispatch, and complete site gate QC.",
                "team": [
                    {"name": "Vikram", "role": "Purchase Manager", "skills": ["Vendor Quotes", "Negotiation", "PO Release"]},
                    {"name": "Priya", "role": "Commercial & GST Analyst", "skills": ["GST Split", "Rate Comparison", "Billing"]},
                    {"name": "Manoj", "role": "Site Store & QC Engineer", "skills": ["Material Testing", "Weighbridge", "Dispatch"]},
                ],
                "tasks": [
                    {"id": "T1", "title": "Float RFQ & Collect 3 Vendor Quotations", "assignee": "Vikram", "dependsOn": [], "days": 2, "rationale": "Vikram manages steel and cement vendor quotes.", "modified": False},
                    {"id": "T2", "title": "Landed Rate & GST Comparison Sheet", "assignee": "Priya", "dependsOn": ["T1"], "days": 2, "rationale": "Priya checks GST slabs, freight, and landed costs.", "modified": False},
                    {"id": "T3", "title": "Release Approved Purchase Order (PO)", "assignee": "Vikram", "dependsOn": ["T2"], "days": 1, "rationale": "Vikram issues PO to selected supplier.", "modified": False},
                    {"id": "T4", "title": "Mill Dispatch & Transit Tracking", "assignee": "Manoj", "dependsOn": ["T3"], "days": 3, "rationale": "Manoj tracks truck dispatch and site arrival.", "modified": False},
                    {"id": "T5", "title": "Weighbridge & Batch Lab Quality Check", "assignee": "Manoj", "dependsOn": ["T4"], "days": 2, "rationale": "Manoj verifies weight and quality before unloading.", "modified": False},
                ],
                "log_summary": "Initialized 5-step civil procurement workflow for 50T TMT steel & 800 bags cement (10-day span).",
                "log_trace": "Chain Step 1 -> Step 2 -> Step 3 completed locally.",
            },
            {
                "id": "proj-default",
                "name": "E-Commerce Checkout Microservice",
                "start": "2026-11-25",
                "deadline": "2026-12-09",
                "req": "Build a payment and checkout service with UPI/card integration, cart validation API, order confirmation webhook, Redis caching, and automated unit + integration tests.",
                "team": [
                    {"name": "Aarav", "role": "Backend Lead", "skills": ["Python", "FastAPI", "Redis", "Payments"]},
                    {"name": "Sneha", "role": "Fullstack Dev", "skills": ["React", "APIs", "Webhooks"]},
                    {"name": "Rohan", "role": "QA & DevOps", "skills": ["Pytest", "Docker", "CI/CD"]},
                ],
                "tasks": [
                    {"id": "T1", "title": "Checkout & Cart Validation API", "assignee": "Aarav", "dependsOn": [], "days": 3, "rationale": "Aarav owns core checkout API design.", "modified": False},
                    {"id": "T2", "title": "UPI & Card Payment Gateway Integration", "assignee": "Aarav", "dependsOn": ["T1"], "days": 4, "rationale": "Aarav handles payment gateway integration.", "modified": False},
                    {"id": "T3", "title": "Order Confirmation Webhook Service", "assignee": "Sneha", "dependsOn": ["T2"], "days": 2, "rationale": "Sneha handles webhook events.", "modified": False},
                    {"id": "T4", "title": "Redis Session & Cart Caching Layer", "assignee": "Aarav", "dependsOn": ["T1"], "days": 2, "rationale": "Parallel caching layer after T1.", "modified": False},
                    {"id": "T5", "title": "Automated Pytest & Docker CI Suite", "assignee": "Rohan", "dependsOn": ["T3", "T4"], "days": 3, "rationale": "Rohan runs automated tests and CI.", "modified": False},
                ],
                "log_summary": "Decomposed software requirements into 5 tasks via local prompt chain (12-day critical path).",
                "log_trace": "Local Chain Step 1 -> Step 2 -> Step 3 completed.",
            },
        ]

        for d in demos:
            c.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (d["id"], d["name"], d["start"], d["deadline"], d["req"], json.dumps(d["team"]), json.dumps(d["tasks"]), now)
            )
            c.execute(
                "INSERT INTO memory_logs (project_id, timestamp, type, summary, trace) VALUES (?, ?, ?, ?, ?)",
                (d["id"], now, "LOCAL_CHAIN_INIT", d["log_summary"], d["log_trace"])
            )
    conn.commit()
    conn.close()


def fetch_all_projects():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, start_date, deadline, requirements, team_json, tasks_json FROM projects ORDER BY rowid ASC")
    rows = c.fetchall()
    projects = []
    for r in rows:
        pid = r[0]
        c.execute("SELECT timestamp, type, summary, trace FROM memory_logs WHERE project_id = ? ORDER BY id ASC", (pid,))
        logs = [{"timestamp": l[0], "type": l[1], "summary": l[2], "trace": l[3]} for l in c.fetchall()]
        projects.append({
            "id": pid,
            "name": r[1],
            "startDate": r[2],
            "deadline": r[3],
            "requirements": r[4],
            "team": json.loads(r[5]),
            "tasks": json.loads(r[6]),
            "memoryLogs": logs,
        })
    conn.close()
    return projects


def local_decompose_and_allocate(requirements: str, team: list):
    # Split requirements by sentence/clause/comma into actionable work items
    raw_parts = [p.strip(" .:-") for p in re.split(r"[.\n;]+", requirements) if len(p.strip(" .:-")) > 4]
    sub_items = []
    for part in raw_parts:
        if "," in part and len(part) > 65:
            sub_items.extend([x.strip() for x in part.split(",") if len(x.strip()) > 4])
        else:
            sub_items.append(part)

    if not sub_items:
        sub_items = ["Requirement Analysis & Setup", "Core Implementation", "Testing & Handover"]

    tasks = []
    for idx, item in enumerate(sub_items[:8], start=1):
        tid = f"T{idx}"
        member = team[(idx - 1) % len(team)] if team else {"name": "Lead", "skills": ["General"]}
        skills_text = ", ".join(member.get("skills", []))
        title = item if len(item) <= 58 else item[:55].rsplit(" ", 1)[0] + "..."
        days = 3 if idx <= 2 else 2
        deps = [f"T{idx - 1}"] if idx > 1 else []
        tasks.append({
            "id": tid,
            "title": title.capitalize(),
            "assignee": member.get("name", "Lead"),
            "dependsOn": deps,
            "days": days,
            "rationale": f"Local skill match: {member.get('name')} covers [{skills_text or 'execution'}].",
            "modified": False,
        })
    return tasks


class NewProjectRequest(BaseModel):
    name: str
    startDate: str
    deadline: str
    requirements: str
    team: list


class ReActUpdateRequest(BaseModel):
    projectId: str
    changeRequest: str


@app.get("/")
def serve_dashboard():
    return FileResponse("index.html")


@app.get("/api/projects")
def get_projects():
    return {"projects": fetch_all_projects()}


@app.post("/api/projects/create")
def create_project_chain(req: NewProjectRequest):
    tasks = local_decompose_and_allocate(req.requirements, req.team)
    pid = f"proj-{int(datetime.now().timestamp())}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trace = (
        f"Stage 1 (Local Decomposition): Parsed requirements into {len(tasks)} subtasks.\n"
        f"Stage 2 (Local Allocation): Matched across {len(req.team)} team members without external API.\n"
        f"Stage 3 (Schedule Engine): Built dependency chain T1..T{len(tasks)}."
    )

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (pid, req.name, req.startDate, req.deadline, req.requirements, json.dumps(req.team), json.dumps(tasks), now)
    )
    c.execute(
        "INSERT INTO memory_logs (project_id, timestamp, type, summary, trace) VALUES (?, ?, ?, ?, ?)",
        (pid, now, "LOCAL_CHAIN_INIT", f"Created '{req.name}' with {len(tasks)} subtasks (0 API calls).", trace)
    )
    conn.commit()
    conn.close()

    return {"projectId": pid, "projects": fetch_all_projects()}


@app.post("/api/projects/react-update")
def react_dynamic_update(req: ReActUpdateRequest):
    projects = fetch_all_projects()
    proj = next((p for p in projects if p["id"] == req.projectId), None)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = proj["tasks"]
    team = proj["team"]
    q = req.changeRequest.lower()

    # Extract explicit task ID like T2 or T4 if mentioned
    id_match = re.search(r"\b(t\d+)\b", q)
    mentioned_id = id_match.group(1).upper() if id_match else None

    # Extract explicit day count if mentioned
    day_match = re.search(r"(\d+)\s*day", q)
    extra_days = int(day_match.group(1)) if day_match else 2

    trace_steps = []
    trace_steps.append({"type": "thought", "text": f"Received change request: '{req.changeRequest}'. Inspecting active task graph first."})
    trace_steps.append({"type": "action", "text": "get_state | {}"})
    trace_steps.append({"type": "obs", "text": f"Loaded {len(tasks)} tasks for '{proj['name']}'."})

    if ("drop" in q or "remove" in q or "cancel" in q) and tasks:
        target = next((t for t in tasks if t["id"] == mentioned_id), None)
        if not target:
            target = next((t for t in tasks if "redis" in t["title"].lower()), None) or tasks[-2] if len(tasks) > 1 else tasks[0]
        tid = target["id"]
        trace_steps.append({"type": "thought", "text": f"Scope reduction requested. Removing {tid} ({target['title']}) and rewiring downstream dependencies."})
        trace_steps.append({"type": "action", "text": f"remove_task | {{\"task_id\": \"{tid}\"}}"})
        tasks = [t for t in tasks if t["id"] != tid]
        for t in tasks:
            t["dependsOn"] = [d for d in t.get("dependsOn", []) if d != tid]
        summary = f"Removed {tid} ({target['title']}) and rewired dependent tasks."
        trace_steps.append({"type": "obs", "text": summary})

    elif ("add" in q or "new" in q or "mandated" in q or "extra task" in q or "invoice" in q or "waterproofing" in q or "tensile" in q):
        new_id = f"T{len(tasks) + 1}"
        parent_id = mentioned_id if (mentioned_id and any(t["id"] == mentioned_id for t in tasks)) else (tasks[-1]["id"] if tasks else "")
        owner = team[1]["name"] if len(team) > 1 else (team[0]["name"] if team else "Lead")
        for m in team:
            if m["name"].lower() in q:
                owner = m["name"]
                break
        clean_title = req.changeRequest.strip()
        if len(clean_title) > 48:
            clean_title = clean_title[:45].rsplit(" ", 1)[0] + "..."
        trace_steps.append({"type": "thought", "text": f"Adding new task {new_id} ({extra_days}d) assigned to {owner} after {parent_id or 'start'}."})
        trace_steps.append({"type": "action", "text": f"add_task | {{\"task_id\": \"{new_id}\", \"days\": {extra_days}, \"assignee\": \"{owner}\"}}"})
        tasks.append({
            "id": new_id,
            "title": clean_title.capitalize(),
            "assignee": owner,
            "dependsOn": [parent_id] if parent_id else [],
            "days": extra_days,
            "rationale": f"Added via local ReAct controller for: {req.changeRequest}",
            "modified": True,
        })
        summary = f"Added {new_id} ({extra_days}d) assigned to {owner} and recalculated schedule."
        trace_steps.append({"type": "obs", "text": summary})

    else:
        # Delay / leave / reassignment on an existing task
        target = next((t for t in tasks if t["id"] == mentioned_id), None)
        if not target:
            for m in team:
                if m["name"].lower() in q:
                    target = next((t for t in tasks if t["assignee"].lower() == m["name"].lower()), None)
                    break
        if not target and tasks:
            target = tasks[min(1, len(tasks) - 1)]

        new_assignee = target["assignee"]
        for m in team:
            if m["name"].lower() in q and m["name"].lower() not in target["assignee"].lower():
                new_assignee = m["name"]
                break
        if new_assignee == target["assignee"] and ("leave" in q or "unavailable" in q or "reassign" in q) and len(team) > 1:
            alt = next((m["name"] for m in team if m["name"] != target["assignee"]), target["assignee"])
            new_assignee = alt

        old_days = int(target.get("days", 2))
        new_days = old_days + extra_days
        target["days"] = new_days
        target["assignee"] = new_assignee
        target["modified"] = True
        target["rationale"] = f"Updated by local ReAct controller (+{extra_days}d / owner {new_assignee}) due to: {req.changeRequest}"

        trace_steps.append({"type": "thought", "text": f"Adjusting {target['id']} ({target['title']}) from {old_days}d to {new_days}d, assignee: {new_assignee}."})
        trace_steps.append({"type": "action", "text": f"update_task | {{\"task_id\": \"{target['id']}\", \"days\": {new_days}, \"assignee\": \"{new_assignee}\"}}"})
        summary = f"Updated {target['id']} to {new_days} days (assignee: {new_assignee}) and shifted downstream dates."
        trace_steps.append({"type": "obs", "text": summary})

    trace_steps.append({"type": "action", "text": f"finish | {{\"summary\": \"{summary}\"}}"})
    trace_steps.append({"type": "obs", "text": "Committed to SQLite memory without using external API quota."})

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trace_text = "\n".join([f"{s['type'].upper()}: {s['text']}" for s in trace_steps])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE projects SET tasks_json = ? WHERE id = ?", (json.dumps(tasks), req.projectId))
    c.execute(
        "INSERT INTO memory_logs (project_id, timestamp, type, summary, trace) VALUES (?, ?, ?, ?, ?)",
        (req.projectId, now, "LOCAL_REACT_UPDATE", summary, trace_text)
    )
    conn.commit()
    conn.close()

    return {
        "summary": summary,
        "traceSteps": trace_steps,
        "projects": fetch_all_projects(),
    }


init_db()
seed_default_projects()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)