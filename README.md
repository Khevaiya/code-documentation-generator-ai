# CodeLens AI — Codebase Intelligence & Documentation Agent

An intelligent, multi-lens codebase documentation and architectural intelligence platform powered by **Google Gemini**. Upload any GitHub repository or ZIP archive to generate comprehensive documentation, interactive **Code Knowledge Graphs (CodeKG)**, executive **Health Scorecards**, consult with an **AI Architecture Copilot**, and export to **Docusaurus, GitHub Wiki, and PR comments** in 1 click.

---

## ✨ 6 Core Superpowers

### 1. 🔮 In-App Interactive Documentation Studio
- **8 Deep Analysis Lenses:** Architecture, Security Audit, Developer Onboarding, Compliance & SOC2, Cost & Scalability, Technical Debt, API Reference, and Executive Summary.
- **Interactive Table of Contents & Search:** Instant navigation across all generated insights.
- **Interactive Mermaid Diagram Lightbox:** Zoom, pan, reset, fullscreen, and 1-click **Export SVG / PNG** for architecture, sequence, and ER diagrams.
- **Dual View Modes:** Seamlessly switch between rich visual layout and raw Markdown.

### 2. 🌐 Code Knowledge Graph (CodeKG) & Blast Radius Visualizer
- **In-Memory Graph Engine:** Constructs an interactive network of Files, Classes, Functions, API Routes, Data Models, and External Libraries via AST parsing.
- **Force-Directed 2D Canvas:** Drag, zoom, filter layers, and inspect node centrality & degrees.
- **Instant Blast Radius Analysis:** Click any file or function to immediately calculate and highlight all upstream callers and downstream dependencies.
- **Circular Dependency & Hub Detection:** Automatically flags architectural anti-patterns and god objects.

### 3. 💬 AI Architecture Copilot ("Chat with Your Codebase")
- **Multi-Turn Session Memory:** Retains full context of past questions.
- **Knowledge Graph Grounding:** Queries the repository's symbol table, AST call hierarchy, and generated lenses.
- **Dynamic Mermaid Generation:** Generates real-time architecture diagrams, sequence flows, and code patches in chat.
- **Evidence-Based Citations:** Every explanation links directly to file paths and line numbers.

### 4. 📊 Visual Executive Health Dashboard & Radar Scorecard
- **Letter Grades (A+ to F) & 0–100 Health Score:**
  - 🛡️ **Security Posture Score** (Secrets scan, dangerous calls, injection vectors)
  - 🏗️ **Architectural Modularity Score** (Coupling, cohesion, circular imports)
  - ⚡ **Performance & Scalability Rating** (Async utilization, file footprints)
  - 🧹 **Maintainability & Tech Debt Index** (Complexity hotspots, documentation)
  - 🧪 **Testing & Reliability Coverage** (Test ratios, CI/CD, Docker)
- **Interactive SVG Radar Chart:** Visualizes 5-pillar architectural balance.
- **Prioritized Remediation Roadmap:** Actionable cards with code diff instructions.

### 5. ⚡ 1-Click Ecosystem Exports
- 🚀 **Docusaurus / VitePress Website (.zip):** Download a full static documentation site with custom configs and sidebars.
- 📚 **GitHub Wiki Repository (.zip):** Pre-structured wiki markdown pages with navigation sidebars.
- 🤖 **GitHub PR Review Markdown:** Formatted collapsible review comments for GitHub Actions or PR reviews.

### 6. 🎨 Real-Time Agent Telemetry Terminal
- Live streaming execution log showing AST symbol extraction, Knowledge Graph network construction, and Gemini synthesis phases.

---

## 🏗️ Project Architecture

```
codebase-agent/
├── backend/                         # FastAPI Python backend
│   ├── app.py                       # REST API & WebSocket/SSE endpoints
│   ├── requirements.txt             # Dependencies
│   ├── .env.example                 # Configuration template
│   ├── core/
│   │   ├── config.py                # Environment & token budgets
│   │   ├── models.py                # Pydantic data models
│   │   ├── context_builder.py       # Smart priority file ranker
│   │   ├── gemini_client.py         # Google Gemini LLM client
│   │   ├── orchestrator.py          # Multi-lens pipeline orchestrator
│   │   └── copilot.py               # AI Architecture Copilot engine
│   ├── analyzer/
│   │   ├── static_analyzer.py       # Regex & heuristic scanner
│   │   ├── graph_engine.py          # AST & Code Knowledge Graph engine
│   │   ├── health_score.py          # Executive Health Scorecard engine
│   │   └── mermaid_validator.py     # Mermaid syntax validator
│   ├── ingestion/                   # ZIP & GitHub clone handlers
│   ├── lenses/                      # Prompt templates per lens
│   └── renderers/                   # Markdown, HTML, PDF, DOCX, PPTX, & Export bundlers
├── frontend/                        # React modern developer frontend
│   ├── package.json
│   ├── .example.env
│   └── src/
│       ├── App.js                   # Main application
│       ├── hooks/useAnalysis.js     # Polling & submission hook
│       └── components/
│           ├── DocStudio.js         # Interactive Documentation Studio
│           ├── KnowledgeGraphViewer.js # 2D Force-Directed CodeKG Canvas
│           ├── HealthDashboard.js   # Executive Scorecard & Radar Chart
│           ├── ArchitectureCopilot.js # Slide-out AI Copilot Drawer
│           ├── ExportModal.js       # 1-Click Ecosystem Export Dialog
│           ├── AgentTerminal.js     # Live Agent Telemetry Terminal
│           ├── InputPanel.js        # File upload & GitHub input
│           ├── PreferenceSelector.js# Lens & format selector
│           └── ResultsPanel.js      # Download manager
└── README.md
```

---

## ⚙️ Quickstart Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Google Gemini API Key** (Free from [Google AI Studio](https://aistudio.google.com))

---

### 1. Backend Setup

```bash
cd backend

# 1. Create and configure environment file
cp .env.example .env    # On Windows: copy .env.example .env

# Set your GEMINI_API_KEY in backend/.env:
# GEMINI_API_KEY=AIzaSy...

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
npm install sharp@latest   # For diagram rasterization in DOCX/PPTX

# 4. Start backend server
uvicorn app:app --reload --port 8000
```
Backend runs at **http://localhost:8000**. Swagger API docs at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

```bash
cd ../frontend

# 1. Install dependencies
npm install

# 2. Start development server
npm start
```
Frontend runs at **http://localhost:3000**.

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service health & metadata |
| `POST` | `/analyze/github` | Trigger analysis for a public GitHub repository |
| `POST` | `/analyze/upload` | Upload a `.zip` archive for analysis |
| `GET` | `/jobs/{job_id}` | Poll job status, telemetry logs, and full doc payload |
| `GET` | `/jobs/{job_id}/graph` | Retrieve Code Knowledge Graph (nodes, edges, metrics) |
| `GET` | `/jobs/{job_id}/blast-radius/{node_id}` | Calculate blast radius for a specific node |
| `POST` | `/jobs/{job_id}/chat` | Multi-turn AI Architecture Copilot query |
| `GET` | `/download/{job_id}/export/{type}` | Export to Docusaurus (.zip), Wiki (.zip), or PR Review |
| `GET` | `/download/{job_id}/{filename}` | Download generated report files |
| `DELETE` | `/jobs/{job_id}` | Clean up job files |

---

## 🛡️ License

MIT License.