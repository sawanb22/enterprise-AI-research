# Frontend Architecture Map & Current State Specification

> **Version:** 0.2.0  
> **Status:** Production-Ready & Verified (`tsc -b && vite build` clean, 0 lint errors)  
> **Workspace Root:** `d:\assignment-modus\frontend`  
> **Framework:** React 19.0 + TypeScript 5.4 + Vite 8.2  
> **Design System:** Obsidian Cyber-Slate Dark Terminal (Glassmorphic, Fluid Units, 100dvh, a11y WCAG 2.2 AA)  
> **Last Verified:** 2026-08-18  

---

## 1. Executive Summary & Core Design Invariants

The EvidenceLab frontend is an enterprise-grade research intelligence dashboard. It translates complex, multi-stage autonomous research pipelines and high-throughput vector RAG workflows into a results-first, auditable, and responsive user experience.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     APP SHELL (App.tsx)                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  MOBILE STICKY HEADER (< 1024px): [≡ Menu]  ✦ EvidenceLab  [🌐 Web / 📑 RAG]  [● Connected] │
├───────────────────────────────┬─────────────────────────────────────────────────────────────┤
│    SIDEBAR / OFF-CANVAS       │                     MAIN WORKSPACE                          │
│  ┌─────────────────────────┐  │  ┌───────────────────────────────────────────────────────┐  │
│  │ Brand & Health Status   │  │  │ Header: Eyebrow · Title · Health & Manual Refresh     │  │
│  ├─────────────────────────┤  │  ├───────────────────────────────────────────────────────┤  │
│  │ Intelligence Switcher   │  │  │ QuestionForm: Dual Mode Pill + Enterprise Context     │  │
│  │  ├── 🌐 Web Projects    │  │  ├───────────────────────────────────────────────────────┤  │
│  │  │    └── Past Runs     │  │  │ PipelineCard: Live Active Bar OR Calm Summary Bar     │  │
│  │  └── 📑 PDF RAG Vaults  │  │  ├───────────────────────────────────────────────────────┤  │
│  │       └── Past Reports  │  │  │ DUAL-MODE WORKSPACE PANES:                            │  │
│  ├─────────────────────────┤  │  │  • Web: Clean Briefing Sheet / 4-Tab Audit View       │  │
│  │ User / Pilot 5★ Quota   │  │  │  • RAG: PDF Dropzone Vault / Clean Publication Sheet  │  │
│  └─────────────────────────┘  │  └───────────────────────────────────────────────────────┘  │
├───────────────────────────────┴─────────────────────────────────────────────────────────────┤
│  SLIDE-OVER DRAWERS & MODALS:                                                               │
│  • EvidenceDrawer (Web: Claims, Verbatim Excerpts, Corroboration Matrix)                   │
│  • CitationDrawer (RAG: Page Provenance, Chunk Index, Cosine Similarity %, Quotes)         │
│  • AuthModal (Supabase Sign In / Sign Up) & QuotaExceededModal (5-Star Pilot Tracker)       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Core Invariants

1. **Results-First Layout**: On completed runs, synthesized findings, executive summaries, and publication-ready sheets are displayed immediately. Users never have to sift through raw pipeline logs unless auditing.
2. **Zero-AI-Slop Publication Views**: Both Web Intelligence and Document RAG feature dedicated "Clean Publication Views" ([`CleanWebReportView.tsx`](file:///d:/assignment-modus/frontend/src/components/CleanWebReportView.tsx) and [`CleanDocumentView.tsx`](file:///d:/assignment-modus/frontend/src/components/CleanDocumentView.tsx)) that format research as executive briefings with footnote citations, structured findings, and responsive bibliography tables.
3. **Full-Spectrum Responsiveness & Screen Metric Hardening**:
   - **Desktop ($\ge 1024\text{px}$)**: Fixed 280px sidebar, 2-column workspace grid (`1.2fr 0.8fr`), expanded tables.
   - **Tablet ($768\text{px} - 1023\text{px}$)**: Collapsible off-canvas drawer, adaptive single/two-column grids, horizontal scroll-snapped tabs.
   - **Mobile ($< 640\text{px}$ / $320\text{px} - 390\text{px}$)**: Sticky top mobile bar, 44px touch targets, full-width segmented mode pill with short labels ("Web" / "Document RAG"), responsive table card transformation, safe-area insets (`100dvh`, `env(safe-area-inset-*)`).
4. **Strict Provenance & Verbatim Auditability**: Every conclusion and section links directly to cited claims, verbatim source excerpts, document page provenance, and cross-source agreement scores.
5. **Adaptive Exponential Polling**: Polling loop starts fast (1.8s) during active runs and backs off (3.6s $\rightarrow$ 7.2s $\rightarrow$ 14.4s $\rightarrow$ 30s cap) while sleeping when runs complete.
6. **Accessible Keyboard & Focus Management**: Focus trapping, `Escape` key dismissal, ARIA states (`aria-expanded`, `aria-controls`), and `:focus-visible` high-contrast rings across all drawers and modals.

---

## 2. Directory Structure & Module Responsibilities

```
frontend/src/
├── api.ts                              # Strongly typed REST API client (DTOs, error handling, auth headers)
├── App.tsx                             # Root orchestrator, mobile navbar, mode routing, drawer states
├── main.tsx                            # React 18 createRoot entry point with AuthProvider wrapper
├── styles.css                          # Complete design system (CSS vars, dark glassmorphism, responsive queries)
├── vite-env.d.ts                       # Vite environment type declarations
│
├── auth/                               # Supabase Authentication & Pilot Quota Subsystem
│   ├── AuthContext.tsx                 # Global AuthProvider, session lifecycle, token refresh, quota state
│   ├── AuthModal.tsx                   # Celestial modal dialog for Sign In & Sign Up
│   ├── LifetimeQuotaBadge.tsx          # Star-based pilot quota indicator pill
│   ├── QuotaExceededModal.tsx          # 5-Star pilot quota breakdown modal with visual star cards
│   ├── UserProfileMenu.tsx             # User profile avatar, quota counter, and sign-out dropdown
│   ├── index.ts                        # Auth module barrel exports
│   ├── supabase.ts                     # Supabase client singleton initialization
│   └── types.ts                        # Auth TypeScript interfaces (User, Session, QuotaStatus)
│
├── components/                         # Modular UI Component Library
│   ├── AssessmentsCard.tsx             # Pairwise claim comparison matrix (supports, qualifies, contradicts)
│   ├── AuditorReportView.tsx           # Deep technical auditor view for raw RAG JSON inspection
│   ├── CitationDrawer.tsx              # Slide-over provenance inspector for RAG PDF citations
│   ├── ClaimsCard.tsx                  # Topic-grouped claims with confidence badges & verbatim toggles
│   ├── CleanDocumentView.tsx           # Executive PDF publication sheet with responsive bibliography table
│   ├── CleanWebReportView.tsx          # Executive Web publication sheet with verified sources table
│   ├── ConclusionsCard.tsx             # Synthesized conclusion statements with deductive reasoning & trace
│   ├── ConnectionIndicator.tsx         # Polling/API connection status pill with manual refresh button
│   ├── DocumentList.tsx                # Uploaded PDF card grid with page counts, SHA-256 hashes, delete actions
│   ├── DocumentUpload.tsx              # Drag-and-drop PDF upload dropzone with progress bar
│   ├── ErrorPanel.tsx                  # Intelligent error classifier (429, timeouts, 0 claims) with 1-click retry
│   ├── EvidenceDrawer.tsx              # Slide-over conclusion-to-claim verbatim evidence trace modal
│   ├── EvidenceQualitySummary.tsx      # Computed grounding scorecard (coverage, agreement, freshness)
│   ├── PipelineCard.tsx                # 6-stage active execution tracker vs calm completed summary bar
│   ├── QuestionForm.tsx                # Dual-mode segmented pill input with guided context accordion
│   ├── RAGReportView.tsx               # RAG report orchestrator (Clean view vs Auditor tabs toggle)
│   ├── RAGWorkspaceTabs.tsx            # RAG workspace view switcher (Vault Documents vs Research Report)
│   ├── ResearchTabs.tsx                # 4-tab Web research controller (Conclusions, Sources, Claims, Activity)
│   ├── Sidebar.tsx                     # Project switcher, historical run accordion, off-canvas mobile drawer
│   ├── SourcesCard.tsx                 # Searchable, filterable library of retrieved web source snapshots
│   ├── StarfieldBackground.tsx         # Animated cosmic background (dust, stars, meteors, reduced-motion a11y)
│   └── WebReportToolbar.tsx            # Web report action bar (Clean vs Tabs toggle, Copy Markdown, Export .md)
│
├── hooks/                              # Custom React Lifecycle & Data Hooks
│   ├── usePolling.ts                   # Adaptive backoff polling loop + connection status detector
│   ├── useRAGData.ts                   # RAG state store (vaults, documents, reports, citations)
│   └── useResearchData.ts              # Web intelligence state store (projects, runs, claims, assessments)
│
└── utils/                              # Helpers, Formatting & Text Processing
    ├── secureStorage.ts                # Session storage wrapper with encryption fallback
    └── textUtils.ts                    # XSS sanitizers (sanitizeText, sanitizeUrl), date formatters, mojibake cleaner
```

---

## 3. Component Hierarchy & Data Flow

```mermaid
graph TD
    Root[main.tsx: AuthProvider] --> App[App.tsx Orchestrator]
    
    App --> MobileHeader[Mobile Sticky Header]
    App --> Sidebar[Sidebar.tsx: Desktop & Mobile Off-Canvas]
    App --> WorkspaceHeader[Workspace Header & ConnectionIndicator]
    App --> QuestionForm[QuestionForm.tsx: Dual-Mode Pill & Context]
    App --> PipelineCard[PipelineCard.tsx: Active Stage vs Calm Summary]
    
    App -->|Mode == 'web'| WebWorkspace[Web Intelligence Workspace]
    App -->|Mode == 'rag'| RAGWorkspace[Document RAG Workspace]
    
    WebWorkspace --> WebReportToolbar[WebReportToolbar.tsx]
    WebWorkspace -->|View == 'clean'| CleanWebReportView[CleanWebReportView.tsx]
    WebWorkspace -->|View == 'tabs'| ResearchTabs[ResearchTabs.tsx: 4-Tab Audit View]
    
    ResearchTabs --> Tab1[Tab 1: ConclusionsCard + EvidenceQualitySummary]
    ResearchTabs --> Tab2[Tab 2: SourcesCard]
    ResearchTabs --> Tab3[Tab 3: ClaimsCard + AssessmentsCard]
    ResearchTabs --> Tab4[Tab 4: RunEvent Pipeline Activity Feed]
    
    RAGWorkspace --> RAGWorkspaceTabs[RAGWorkspaceTabs.tsx]
    RAGWorkspace -->|Tab == 'vault'| VaultPane[DocumentUpload.tsx + DocumentList.tsx]
    RAGWorkspace -->|Tab == 'report'| CleanDocumentView[CleanDocumentView.tsx]
    
    CleanDocumentView -.->|Click [DOC-X • p.Y]| CitationDrawer[CitationDrawer.tsx: RAG Provenance]
    ConclusionsCard -.->|Click Inspect Trace| EvidenceDrawer[EvidenceDrawer.tsx: Web Claim Trace]
    
    App --> AuthModal[AuthModal.tsx: Sign In / Up]
    App --> QuotaExceededModal[QuotaExceededModal.tsx: 5★ Pilot Limit]
```

---

## 4. Component Deep Dive & Specifications

### 4.1 `App.tsx` — Root Layout & Orchestrator
- **State Management**:
  - `mode`: `"web"` | `"rag"` (persisted in `sessionStorage`).
  - `webReportMode`: `"clean"` | `"tabs"` (persisted in `sessionStorage`).
  - `ragActiveTab`: `"vault"` | `"report"`.
  - `isMobileNavOpen`: Boolean controlling the mobile slide-out drawer.
  - Active drawers: `evidenceDrawerOpen`, `activeCitation`.
- **Mobile Navbar (`.mobile-header`)**:
  - Sticky top bar (`height: calc(54px + var(--sat))`) visible only at `< 1024px`.
  - Animated 3-line hamburger morphing into `✕` with ARIA attributes.
  - Live mode pill (`🌐 Web` / `📑 RAG`) and connection status dot.
- **Error Handling**: Catches 429 quota exceptions and triggers `QuotaExceededModal`.

### 4.2 `Sidebar.tsx` — Project Switcher & Off-Canvas Mobile Drawer
- **Dual View Modes**:
  - *Web Intelligence Mode*: Displays list of research projects with historical runs, execution status pills (`completed`, `partial`, `failed`), and 1-click retry buttons.
  - *Document RAG Mode*: Displays PDF document vaults with uploaded document counters and historical generated reports.
- **Mobile Drawer Transitions**:
  - Slides from `translateX(-100%)` to `translateX(0)` with `0.28s cubic-bezier(0.16, 1, 0.3, 1)`.
  - Full backdrop blur overlay (`.sidebar-backdrop`) with `z-index: 95`.
  - `Escape` key listener and auto-closing on any project/run selection.
- **User Footer**: Displays user avatar, email, and active 5-star pilot quota badge.

### 4.3 `QuestionForm.tsx` — Segmented Mode Input & Guided Enterprise Context
- **Fluid Segmented Mode Pill**:
  - Toggle between `🌐 Web Intelligence` and `📑 Enterprise Document RAG`.
  - Responsive text scaling: switches from `.mode-label-full` ("Enterprise Document RAG") to `.mode-label-short` ("Document RAG") on mobile screens $< 640\text{px}$.
- **Guided Context Accordion**:
  - *Target Audience*: Executive, Technical, Compliance, General.
  - *Geographic Scope*: Global, North America, EMEA, APAC, etc.
  - *Time Horizon*: Last 12 months, Last 3 years, Historical.
  - *Evidence Preference*: Peer-reviewed, Regulatory filings, Official benchmarks.
  - *Research Goal*: Market landscape, Risk assessment, Feasibility study.

### 4.4 `CleanDocumentView.tsx` & `CleanWebReportView.tsx` — Clean Publication Sheets
- **Clean Document View (PDF RAG)**:
  - Executive Overview & Synthesis summary.
  - Structured Findings sections with inline superscript citations (`[1]`, `[2]`).
  - **Responsive Bibliography Table**: Automatically transforms from a 5-column table on desktop into a stacked, readable card list on mobile viewports $< 640\text{px}$ using CSS `data-label` selectors.
  - Scope & Limitations footnote callout.
- **Clean Web Report View (Web Intelligence)**:
  - Key Findings executive briefing.
  - Verified Sources Table with publisher, source type, canonical URLs, and direct visit links.

### 4.5 `CitationDrawer.tsx` & `EvidenceDrawer.tsx` — Slide-Over Provenance Inspectors
- **Citation Drawer (RAG)**:
  - Provenance Trace header with Citation $N$ of $M$ counter and next/previous navigation.
  - Target Document Card with page number, chunk index, and cosine relevance percentage.
  - Exact verbatim quote card with highlighted excerpt.
  - Safe-area close button (`right: 12px; top: 12px;`) and stacked mobile footer buttons.
- **Evidence Drawer (Web Intelligence)**:
  - Traces synthesized conclusions to supporting, qualifying, or contradicting claims.
  - Displays exact source character offsets (`excerpt_start`, `excerpt_end`) in the raw snapshot.

### 4.6 `DocumentUpload.tsx` & `DocumentList.tsx` — PDF Knowledge Vault
- **Document Upload**:
  - Drag-and-drop PDF zone with multi-file support.
  - Validates `%PDF` magic bytes and 50MB file size limit before upload.
  - Live progress bar and status feedback.
- **Document List**:
  - Card grid displaying filename, page count, upload timestamp, and SHA-256 hash pill.
  - Status badges: `pending` (yellow), `processing` (blue spinner), `completed` (green checkmark), `failed` (red).
  - 36×36px touch-friendly delete button with confirmation dialog.

### 4.7 `AuthModal.tsx` & `QuotaExceededModal.tsx` — Auth & Pilot Quotas
- **AuthModal**:
  - Celestial glassmorphic overlay for Supabase Authentication.
  - Tab switcher between "Sign In" and "Create Account".
  - Secure credential submission with error banner.
- **QuotaExceededModal**:
  - Displays 5 visual star cards representing the 5 free lifetime research runs.
  - Categorizes consumed stars (`✧ Consumed`) vs available stars (`★ Ready`).
  - Explains pilot evaluation limits while reassuring users that existing data remains accessible.

### 4.8 `StarfieldBackground.tsx` — Atmospheric Canvas & Performance Optimization
- **Layers**:
  - 3 deep breathing nebular aurora gradients.
  - 70 twinkling cosmic stars with randomized size, opacity, and duration.
  - 12 wandering dust particles with colored shadows.
  - 3 shooting meteors.
- **Performance & a11y Hardening**:
  - Layer hints: `will-change: transform, opacity;`.
  - Reduces active particles on mobile devices (`@media (max-width: 768px)`).
  - Respects `@media (prefers-reduced-motion: reduce)` by disabling all animations.

---

## 5. State Management & Custom Hooks

### 5.1 `useResearchData.ts` — Web Intelligence Store
```typescript
interface UseResearchDataReturn {
  projects: ResearchProject[];
  activeProject?: ResearchProject;
  run?: ResearchRun;
  sources: SourceSnapshot[];
  claims: Claim[];
  assessments: EvidenceAssessment[];
  conclusions: Conclusion[];
  events: RunEvent[];
  planItems: PlanItem[];
  loading: boolean;
  error?: string;
  createProjectAndRun: (question: string, context?: ResearchContext) => Promise<void>;
  retryRun: (runId: string) => Promise<void>;
  openProject: (project: ResearchProject) => void;
  openRunById: (runId: string) => Promise<void>;
  refreshActiveRun: () => Promise<void>;
}
```

### 5.2 `useRAGData.ts` — Enterprise Document RAG Store
```typescript
interface UseRAGDataReturn {
  vaults: RAGVault[];
  activeVault?: RAGVault;
  documents: DocumentItem[];
  report?: RAGReport;
  pastReports: RAGReport[];
  loading: boolean;
  uploading: boolean;
  generating: boolean;
  error?: string;
  createVault: (name: string, description?: string) => Promise<RAGVault>;
  uploadDocuments: (files: File[]) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  generateRAGReport: (question: string) => Promise<void>;
  openVault: (vaultId: string) => Promise<void>;
  openReportById: (reportId: string) => Promise<void>;
}
```

### 5.3 `usePolling.ts` — Adaptive Exponential Backoff Polling
- **Interval Formula**: `currentInterval = Math.min(initialInterval * Math.pow(backoffFactor, attempts), maxInterval)` (1.8s $\rightarrow$ 3.6s $\rightarrow$ 7.2s $\rightarrow$ 14.4s $\rightarrow$ 30s cap).
- **Status State**: Detects `connected`, `connecting`, `offline`, and `error` states.
- **Manual Trigger**: `manualRefresh()` forces immediate polling execution.

---

## 6. API Client & Interface Contracts (`api.ts`)

The API client provides strongly typed methods communicating with the FastAPI backend:

| Method | Endpoint | Description | Auth Required |
|:---|:---|:---|:---|
| `getBootstrapData()` | `GET /api/v1/workspace/bootstrap` | Bootstraps all projects, vaults, and active states | Optional |
| `createResearchProject()` | `POST /api/v1/research-projects` | Initiates new Web Intelligence research run | Optional / Quota |
| `getRunDetail(runId)` | `GET /api/v1/research-runs/{id}` | Retrieves full run data (claims, conclusions, events) | No |
| `retryResearchRun(runId)` | `POST /api/v1/research-runs/{id}/retry` | Resumes a failed/partial run from last stage | Optional / Quota |
| `getTraceDetail(conclusionId)` | `GET /api/v1/conclusions/{id}/trace` | Retrieves claim-to-source verbatim trace | No |
| `createRAGVault(name)` | `POST /api/v1/rag-vaults` | Creates a new PDF document vault | Optional |
| `uploadDocument(vaultId, file)` | `POST /api/v1/projects/{id}/documents` | Uploads PDF with background ingestion | Optional |
| `deleteDocument(docId)` | `DELETE /api/v1/documents/{id}` | Removes document and vector embeddings | Optional |
| `executeRAGResearch(vaultId, q)`| `POST /api/v1/projects/{id}/rag-research` | Executes pgvector RAG + FlashRank synthesis | Optional / Quota |
| `getRAGReport(reportId)` | `GET /api/v1/rag-reports/{id}` | Retrieves generated RAG report with citations | No |
| `getUserProfile()` | `GET /api/v1/auth/me` | Fetches active user profile and quota | Bearer JWT |

---

## 7. Responsive Design System & CSS Specifications (`styles.css`)

### 5-Tier Responsive Breakpoint Matrix

| Breakpoint | Target Devices | Key Adaptations |
|:---|:---|:---|
| **$\ge 1024\text{px}$** | Desktop, Laptops, 4K | Fixed 280px sidebar, 2-column workspace grid (`1.2fr 0.8fr`), full table columns, hidden mobile header. |
| **$768\text{px} - 1023.98\text{px}$** | Tablets, iPads | Sticky `.mobile-header` enabled, sidebar becomes off-canvas drawer (`min(320px, 85vw)`), single-column workspace grid, scroll-snapped tabs. |
| **$640\text{px} - 767.98\text{px}$** | Large Phones (Landscape) | Columnar workspace headers, full-width telemetry widgets, drawer width set to `100vw`. |
| **$480\text{px} - 639.98\text{px}$** | Standard Phones (Portrait) | Mode pill switches to short labels (`Web` / `Document RAG`), table converts to stacked card mode via `data-label`, toolbars stack vertically. |
| **$320\text{px} - 479.98\text{px}$** | Compact Phones (iPhone SE) | Fluid clamp padding (`14px 10px`), 5-star quota cards wrap cleanly (`minmax(54px, 1fr)`), drawer buttons stack vertically with 44px touch targets. |

### Accessibility & Motion Hardening
- **WCAG 2.2 Touch Target Compliance**: All interactive buttons, tabs, checkbox pills, and close buttons enforce $\ge 44\times 44\text{px}$ touch targets.
- **Focus Rings**: `:focus-visible { outline: 2px solid var(--accent-blue) !important; outline-offset: 2px !important; }`.
- **Safe Area Insets**: Handled via CSS custom properties:
  ```css
  --sat: env(safe-area-inset-top, 0px);
  --sab: env(safe-area-inset-bottom, 0px);
  --sal: env(safe-area-inset-left, 0px);
  --sar: env(safe-area-inset-right, 0px);
  ```
- **Reduced Motion**: Respects user preferences via `@media (prefers-reduced-motion: reduce)` by disabling background star animations, meteor streaks, and speeding up transitions.
