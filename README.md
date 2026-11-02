# ScopePilot AI

**Intelligent project scoping and proposal automation platform**

ScopePilot AI converts vague customer requirements into structured project specifications, validates them through an iterative verifier-feedback architecture, generates verified proposals, and routes them for human approval through Zoho Cliq.

## Architecture (strict)

```
2 LLM-BACKED AGENTS
  ├── Scope Intelligence Agent  → Llama via OpenRouter
  └── Verifier-Loop Agent       → Mistral via OpenRouter

+ DETERMINISTIC SHELL AGENTS
  ├── Parser Agent
  ├── Proposal Generator
  ├── Estimation Agent
  └── Approval Handler

+ ONE WORKFLOW ORCHESTRATOR (agent_flow.py)
+ FastAPI public REST API
+ gRPC internal agent communication
+ PostgreSQL + SQLAlchemy 2.x (async)
+ Python MCP Server (tool interface)
+ Zoho SalesIQ (discovery) + Zoho Cliq (approval)
```

**No additional LLM agents, no hidden AI fallbacks, no third-party AI orchestration frameworks.**

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenRouter API key (https://openrouter.ai)

### 1. Clone & configure

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENROUTER_API_KEY
```

### 2. Launch

```bash
docker compose up --build
```

API will be available at http://localhost:8000  
Interactive docs: http://localhost:8000/docs

### 3. Create a project & run the workflow

```bash
# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Portal MVP",
    "original_prompt": "We need a simple web portal where our customers can log in, view invoices and download PDF statements. Should work on mobile too. We want it in about 8 weeks.",
    "customer": {"name": "Acme Corp", "email": "pm@acme.com"}
  }'

# Run the full pipeline (parse → scope → verify ↔ correct → proposal)
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/run
```

## Core Flow

```
CUSTOMER INPUT
    ↓
SHELL / PARSER AGENT          (deterministic)
    ↓
STRUCTURED REQUIREMENTS
    ↓
MISSING INFO CHECK ──────────► NEEDS_CUSTOMER_INPUT
    ↓
SCOPE INTELLIGENCE AGENT      (Llama / OpenRouter)
    ↓
DRAFT SCOPE
    ↓
VERIFIER-LOOP AGENT           (Mistral / OpenRouter)
    ↓
(feedback loop until verified)
    ↓
PROPOSAL GENERATOR            (deterministic)
    ↓
ESTIMATION AGENT              (deterministic)
    ↓
APPROVAL HANDLER              (Zoho Cliq)
```

## License

MIT
