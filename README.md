# AI Model Governance Workbench

Governed AI release control plane for managing LLM-based systems with deterministic evaluation gates, structured approvals, incident linkage, and rollback workflows.

This project demonstrates how production-grade AI systems should be governed—not just deployed.

---

## Overview

AI systems are not static artifacts. They evolve through prompt changes, model updates, and configuration tuning. This workbench provides a **control plane** to manage that lifecycle safely.

Core capabilities:

- Versioned AI artefacts (systems, prompts, model configs)
- Deterministic evaluation pipelines with thresholds
- Risk-tier driven approval workflows
- Incident-aware promotion blocking
- Controlled rollback to known-good baselines
- Immutable audit trail for all actions

---

## System Architecture

The platform is composed of:

- **Backend:** Django + Django REST Framework  
- **Frontend:** React + TypeScript + React Query + Zod  
- **Database:** SQLite (local), easily swappable  
- **Evaluation Engine:** deterministic dataset runner with threshold gating  

High-level flow:

```

Draft → Submitted → Eval Runs → (Pass/Fail)
→ Pending Approval → Approved → Active
→ (Incidents) → Rollback

```

---

## Core Concepts

### 1. AI Systems
Top-level governed entities.

Each system has:
- Risk tier (low / medium / high / critical)
- Owners (technical + business)
- Active release

---

### 2. Release Candidates

A release candidate is a snapshot of:

- Prompt version
- Model configuration
- System context

Lifecycle states:

- `draft`
- `submitted`
- `eval_failed`
- `pending_approval`
- `approved`
- `active`
- `rolled_back`

---

### 3. Evaluation Gates

Each release candidate is evaluated against datasets:

- baseline
- adversarial
- regression

Metrics include:

- accuracy
- latency (p95, mean)
- schema validity
- cost estimate
- timeout rate

Each metric has strict thresholds.  
Failure blocks promotion.

---

### 4. Approval Workflow

Approval requirements depend on system risk tier:

| Risk Tier | Required Approvals |
|----------|------------------|
| Low      | Technical        |
| Medium   | Technical + Product |
| High     | Technical + Product + Risk |
| Critical | Technical + Product + Risk + Governance |

Each approval record supports:

- approve
- reject
- request changes

---

### 5. Incidents

Operational incidents are linked to releases and systems.

- Can block promotion
- Drive rollback decisions
- Classified by severity:
  - low / medium / high / critical

---

### 6. Rollback

Rollback restores a previously approved release when:

- incidents occur
- production degradation is detected

Rollback is blocked if:
- no valid rollback target exists
- governance constraints are violated

---

### 7. Audit Trail

Every action generates an immutable audit event:

- submissions
- eval runs
- approvals
- promotions
- rollbacks
- incidents

---

## Demo Walkthrough

### Systems Registry

`screenshots/systems.png`

- View governed AI systems
- Inspect active releases
- Observe ownership and risk tier

---

### Approval Queue

`screenshots/approvals.png`

- Filter by decision and approval type
- Review pending approvals
- Approve / reject / request changes

---

### Incident Dashboard

`screenshots/incidents.png`

- View operational incidents
- Identify promotion blockers
- Inspect linked releases

---

### Audit & Metrics

`screenshots/audit.png`

- Timeline of governance events
- System-wide metrics
- Blocker visibility

---

## Local Setup

### 1. Backend

Path:
```

D:\AI-Projects\ai-model-governance-workbench\backend

````

Run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
````

Long-running: yes
Press CTRL + C to stop server

---

### 2. Seed Demo Data

```powershell
python ..\infra\scripts\seed_demo_data.py
```

This creates:

* systems
* prompts
* model configs
* release candidates
* eval runs
* approvals
* incidents
* rollback records

---

### 3. Frontend

Path:

```
D:\AI-Projects\ai-model-governance-workbench\frontend
```

Run:

```powershell
cd frontend
npm install
npm run dev
```

Long-running: yes
Press CTRL + C to stop dev server

---

### 4. Access UI

* Frontend: [http://localhost:5173](http://localhost:5173)
* Backend API: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

---

## Example Seeded Scenario

The demo includes:

* A **critical system** (Evidence Extractor)
* A **failed evaluation candidate**
* A **pending approval candidate**
* A **production incident**
* A **rollback event**

This demonstrates:

* Promotion blocking via eval failures
* Approval queue workflow
* Incident-driven rollback

---

## Tech Stack

Frontend:

* React
* TypeScript
* React Query
* Zod

Backend:

* Django
* Django REST Framework

---

## Roadmap

* CI pipeline with lint + type checks
* Deployment configuration
* Role-based access controls
* Multi-environment promotion (dev → staging → prod)

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Cherry Augusta

See the [LICENSE](./LICENSE) file for full details.

---