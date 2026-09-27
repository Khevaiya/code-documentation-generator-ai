# CodeLens AI — Codebase Documentation & Analysis Agent

An intelligent, multi-lens codebase documentation and analysis agent powered by Google Gemini. Upload a GitHub repository URL or a ZIP archive, choose your analysis lenses and target audience, and generate professional documentation in multiple formats (Markdown, Word DOCX, PDF, Interactive HTML, PowerPoint PPTX) in minutes.

---

## ✨ Key Features

### 🔍 8 Analysis Lenses
- **Architecture** — High-level system design, design patterns, microservices/component relationships, and data flows.
- **Security** — SAST-style vulnerability scanning, secret detection, input sanitization, and security best practices.
- **Onboarding** — Developer quickstart guide, environment prerequisites, folder structure walkthrough, and key workflows.
- **Compliance** — SOC2, GDPR, HIPAA, and OWASP Top 10 compliance readiness audits.
- **Cost Optimization** — Infrastructure resource usage, efficiency recommendations, and performance bottlenecks.
- **Technical Debt** — Code smell detection, cyclomatic complexity hotspots, and maintainability metrics.
- **API Consumer** — REST/GraphQL endpoint catalogs, authentication schemes, payload schemas, and integration recipes.
- **Executive Summary** — Business-aligned technical overview, risk analysis, and modernization roadmap.

### 📄 5 Output Formats
- **Markdown** (`.md`) — Clean, version-control friendly format ready for Git repositories or wikis.
- **Word Document** (`.docx`) — Formatted report with styling, tables, and embedded high-resolution diagrams.
- **PDF** — Print-ready document with custom typography, headers/footers, and page breaks.
- **Interactive HTML** — Modern, responsive web report featuring collapsible sections and diagram viewer.
- **PowerPoint** (`.pptx`) — Visual slide deck suitable for executive presentations and technical reviews.

### 🎨 Core Capabilities
- **Visual Mermaid Diagrams** — Auto-generated Architecture, Sequence, and ER diagrams embedded directly in output files.
- **Evidence-Based Citations** — Findings link to specific files and line numbers.
- **Intelligent Gap Detection** — Flags missing unit tests, undocumented endpoints, absent error boundaries, and unhandled exceptions.
- **Audience-Targeted Formatting** — Tailor the technical depth for CTOs, Software Engineers, Compliance Auditors, or Product Managers.

---

## 🏗️ Project Structure

```
codebase-agent/
├── backend/                     # FastAPI Python backend
│   ├── app.py                   # FastAPI application & REST endpoints
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Backend environment template
│   ├── core/                    # Config, data models, Gemini client, orchestrator
│   ├── ingestion/               # ZIP & GitHub ingestion handlers
│   ├── analyzer/                # Static analysis & Mermaid validation
│   ├── lenses/                  # Prompt engineering & analysis lenses
│   └── renderers/               # Markdown, HTML, PDF, DOCX, & PPTX renderers
├── frontend/                    # React frontend application
│   ├── package.json
│   ├── .example.env             # Frontend environment template
│   └── src/
│       ├── App.js               # Main application component
│       ├── hooks/               # Custom hooks for job polling & submission
│       └── components/          # UI components (InputPanel, PreferenceSelector, ResultsPanel, etc.)
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites

| Requirement | Details |
|---|---|
| **Python 3.10+** | Recommended: Python 3.11, 3.12, or 3.13 |
| **Node.js 18+** | For running the React frontend and diagram rasterization |
| **Google Gemini API Key** | Get a free API key at [Google AI Studio](https://aistudio.google.com) |

---

### 1. Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and configure `.env`:**
   ```bash
   # Windows
   copy .env.example .env

   # macOS / Linux
   cp .env.example .env
   ```
   Open `.env` and set your `GEMINI_API_KEY`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

3. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Sharp for diagram conversion (in backend directory):**
   ```bash
   npm install sharp@latest
   ```

6. **Start the backend server:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```
   The backend API will run at **http://localhost:8000**. Swagger API docs are accessible at **http://localhost:8000/docs**.

---

### 2. Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd ../frontend
   ```

2. **Create and configure `.env` (optional):**
   ```bash
   # Windows
   copy .example.env .env

   # macOS / Linux
   cp .example.env .env
   ```

3. **Install dependencies:**
   ```bash
   npm install
   ```

4. **Start the development server:**
   ```bash
   npm start
   ```
   The application will open at **http://localhost:3000**.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status and metadata |
| `POST` | `/analyze/github` | Trigger analysis for a public GitHub repository |
| `POST` | `/analyze/upload` | Upload a `.zip` archive for analysis |
| `GET` | `/jobs/{job_id}` | Poll the status and progress of an analysis job |
| `GET` | `/download/{job_id}/{filename}` | Download generated report files |
| `DELETE` | `/jobs/{job_id}` | Clean up job files and temporary artifacts |
| `GET` | `/health` | Service health check |

---

## 💡 Usage

1. Open **http://localhost:3000** in your browser.
2. Enter a **GitHub Repository URL** or drag and drop a **ZIP archive** of your project.
3. Select the **Analysis Lenses** you want to generate (Architecture, Security, etc.).
4. Choose the desired **Output Formats** (Markdown, PDF, DOCX, HTML, PPTX).
5. Optionally specify an **Audience Role** (e.g., Engineer, CTO, Auditor).
6. Click **Analyze Codebase** and watch the real-time progress.
7. Download your generated documentation files once complete!

---

## 🛡️ License

MIT License.