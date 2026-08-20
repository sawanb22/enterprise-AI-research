# 🚀 EvidenceLab Production Deployment Guide
**Target Stack:** Vercel (Frontend SPA) + Railway (FastAPI Monolith) + Supabase (PostgreSQL 17 & Auth)  
**Domains:** Free subdomains (`*.vercel.app` & `*.up.railway.app`)  
**Storage Architecture:** Pure Ephemeral Container Disk (No volumes needed; 100% of intelligence, text, vectors, and history live in Supabase PostgreSQL)

---

## 1. Railway Free Credits & Runtime Breakdown

* **Monthly Free Credit:** Railway provides **$5.00 in free usage credit** every month on the Hobby tier.
* **Service Consumption:** A lightweight FastAPI monolith using $\approx 150\text{MB}$ RAM and minimal idle CPU costs $\approx \mathbf{\$2.00\text{ to }\$2.80\text{ per month}}$.
* **Continuous 24/7 Runtime:** $5.00 easily covers the full **744 hours in a 31-day month** without hitting credit limits.
* **Volume Cost:** Because we are **not** attaching a persistent volume, volume disk costs are **$0.00**.

---

## 2. Hardened Infrastructure Files Already Configured in Codebase

| File | Purpose |
| :--- | :--- |
| [`frontend/vercel.json`](file:///d:/assignment-modus/frontend/vercel.json) | SPA client-side routing fallback (`/(.*)` $\rightarrow$ `/index.html`) + HTTP security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`). |
| [`backend/Procfile`](file:///d:/assignment-modus/backend/Procfile) | Dynamic port binding (`uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`). |
| [`backend/railway.json`](file:///d:/assignment-modus/backend/railway.json) | Nixpacks build configuration, `/api/v1/health` healthcheck, and auto-restart policy. |
| [`backend/app/main.py`](file:///d:/assignment-modus/backend/app/main.py) | Dynamic CORS regex (`allow_origin_regex=r"^https://.*\.vercel\.app$"`) so any deployed Vercel URL is accepted out-of-the-box. |

---

## 3. Step-by-Step Deployment Instructions

```
[ Step 1: Git Push ] ───> [ Step 2: Railway Backend ] ───> [ Step 3: Vercel Frontend ] ───> [ Step 4: Supabase Redirects ]
```

### STEP 1: Commit & Push Code to GitHub
Run the following in your terminal:
```bash
git add .
git commit -m "feat: production deployment configs and security hardening"
git push origin main
```

---

### STEP 2: Deploy Backend to Railway
*(Must be done first so you can get the live backend URL)*

1. Log into **[Railway.app](https://railway.app)**.
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo** $\rightarrow$ select your repository.
3. Click the newly created service box $\rightarrow$ click **Settings**:
   * **Root Directory:** Set to `backend`
   * **Build Command:** Leave empty (Railway automatically uses Nixpacks).
4. Go to the **Variables** tab and add your production environment keys:

```dotenv
AI_PROVIDER=bedrock
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_token
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
EMBEDDING_MODEL_ID=cohere.embed-english-v3.0
TAVILY_API_KEY=your_tavily_key

DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-pooler.supabase.com:6543/postgres?sslmode=require

SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
ALLOWED_ORIGINS=http://localhost:5173
```

5. Go to **Settings** $\rightarrow$ **Networking** $\rightarrow$ click **Generate Domain**.
6. Copy your generated backend URL (e.g., `https://evidencelab-backend-production.up.railway.app`).
7. **Verify Health:** Visit `https://<your-railway-url>/api/v1/health` in your browser. You should see `{"status":"ok", ...}`.

---

### STEP 3: Deploy Frontend to Vercel

1. Log into **[Vercel.com](https://vercel.com)**.
2. Click **Add New** $\rightarrow$ **Project** $\rightarrow$ import your GitHub repository.
3. In the setup wizard:
   * **Framework Preset:** `Vite`
   * **Root Directory:** Click **Edit** and choose `frontend`.
4. Open the **Environment Variables** accordion and add:

```dotenv
VITE_API_URL=https://<your-railway-backend-url>/api/v1
VITE_SUPABASE_URL=https://[project-ref].supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_POSTHOG_PROJECT_TOKEN=your_posthog_project_token
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

5. Click **Deploy**.
6. Copy your live Vercel URL (e.g., `https://evidencelab-frontend.vercel.app`).

---

### STEP 4: Configure Supabase Authentication Redirects

1. Open the **[Supabase Dashboard](https://supabase.com/dashboard)**.
2. Go to **Authentication** $\rightarrow$ **URL Configuration**.
3. **Site URL:** Paste your live Vercel URL:
   ```text
   https://<your-vercel-app>.vercel.app
   ```
4. **Redirect URLs:** Add the following entries:
   * `https://<your-vercel-app>.vercel.app/**`
   * `http://localhost:5173/**`
5. Click **Save**.

---

## 4. Post-Deployment Verification Checklist

| Test Item | Verification Flow | Expected Result |
| :--- | :--- | :--- |
| **1. Cold Load** | Visit `https://<your-vercel-app>.vercel.app` | Interface loads in < 1s with Starfield theme and clean UI. |
| **2. Auth Flow** | Sign in or Sign up | Authenticates in < 0.1ms using local PyJWT verification. Quota badge reads `5 Free Runs`. |
| **3. Web Research** | Ask a question in Web mode | Background task streams through Planning $\rightarrow$ Discovery $\rightarrow$ Claims $\rightarrow$ Synthesis. |
| **4. Instant SWR Reload** | Press **F5 (Refresh)** | Sidebar & inquiry history load **instantly (0ms)** from user-hashed `sessionStorage`. |
| **5. PDF Ingestion** | Upload a research PDF in Document Vault | PyMuPDF extracts pages, computes Cohere embeddings, and saves 100% into Supabase PostgreSQL. |
| **6. Document RAG** | Ask a question about uploaded documents | Vector search + FlashRank rerank synthesizes evidence report with clickable page citations. |

---

## 5. Important Maintenance Rules

1. **Vite Build-Time Environment Baking:**
   * Vite compiles `VITE_API_URL` directly into the JavaScript files during build time.
   * If you ever update the Railway backend domain, navigate to Vercel $\rightarrow$ **Deployments** $\rightarrow$ **Redeploy** to regenerate the bundle.
2. **Zero Volume Maintenance:**
   * You do **not** need to monitor disk usage or clear files on Railway. The temporary files are ephemeral, while all persistent research data lives permanently inside your Supabase PostgreSQL database.
