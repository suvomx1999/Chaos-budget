# Chaos Budget

> **How much of your career is really you?**

Chaos Budget is a counterfactual career simulation engine that decomposes your professional trajectory into **skill**, **luck**, and **timing**. Users submit their career timeline — via a structured form, pasted resume text, or PDF upload — and the system runs 1,000 Monte Carlo simulations at every identified pivot point, applies causal inference to isolate genuine skill effects, and delivers a quantified "Chaos Coefficient" alongside an AI-generated narrative of the alternate yous that could have been.

The system combines a Markov-chain career progression model with DoWhy causal estimation (backdoor linear regression on synthetic counterfactuals) using a 70/30 blend of simulation-derived and causally-estimated luck scores. The result is a rigorous, reproducible breakdown of how circumstance shaped each career — not a horoscope, but a statistical audit.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                 │
│                  React · Vite · TailwindCSS                        │
│                  Framer Motion · Recharts                          │
│                                                                    │
│  ┌────────┐  ┌─────────┐  ┌────────────┐  ┌───────────────────┐  │
│  │  Home  │→ │  Input   │→ │  Results   │→ │  Stripe Paywall   │  │
│  │  Page  │  │  Page    │  │  (free)    │  │  → Full Analysis  │  │
│  └────────┘  └─────────┘  └────────────┘  └───────────────────┘  │
│                      │           │                                  │
└──────────────────────┼───────────┼──────────────────────────────────┘
                       │           │  HTTP/JSON
                       ▼           ▼
┌────────────────────────────────────────────────────────────────────┐
│                           BACKEND                                  │
│                   FastAPI · Python · Uvicorn                        │
│                                                                    │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐  ┌────────┐ │
│  │  Timeline   │  │  Simulator    │  │  Explainer   │  │Payment │ │
│  │  Parser     │  │  (Monte Carlo │  │  (Groq LLM)  │  │(Stripe)│ │
│  │  (Groq LLM) │  │   + DoWhy)   │  │              │  │        │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └───┬────┘ │
│         │                │                  │              │       │
└─────────┼────────────────┼──────────────────┼──────────────┼───────┘
          │                │                  │              │
          ▼                ▼                  ▼              ▼
   ┌──────────────┐  ┌──────────┐    ┌──────────────┐  ┌────────┐
   │  Groq API    │  │ MongoDB  │    │  Groq API    │  │ Stripe │
   │  (parsing)   │  │  Atlas   │    │  (narrative) │  │  API   │
   └──────────────┘  └──────────┘    └──────────────┘  └────────┘
```

---

## Local Setup

### Prerequisites

- **Python 3.11+** (tested with 3.12.7 on Apple Silicon)
- **Node.js 18+** (tested with 20.17)
- **MongoDB Atlas** cluster (free M0 works)
- **Groq API key** — [console.groq.com](https://console.groq.com)
- **Stripe test keys** — [dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)

### 1. Clone & install backend

```bash
cd chaos-budget/backend
python -m venv venv
source venv/bin/activate          # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual keys (see table below)
```

### 3. Start backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 4. Install & start frontend

```bash
cd chaos-budget/frontend
npm install
npm run dev     # → http://localhost:5173
```

### 5. Open the app

Navigate to `http://localhost:5173` — paste a resume or build a timeline, then hit **Analyze**.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key for LLM parsing & narrative |
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | | Database name (default: `chaos_budget`) |
| `ENVIRONMENT` | | `development` / `staging` / `production` |
| `CORS_ORIGINS` | | Comma-separated allowed origins |
| `STRIPE_SECRET_KEY` | | Stripe secret key (for payment) |
| `STRIPE_PUBLISHABLE_KEY` | | Stripe publishable key |
| `STRIPE_PRICE_AMOUNT` | | Price in smallest unit (default: `99`) |
| `STRIPE_CURRENCY` | | Currency code (default: `inr`) |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health + DB status |
| `POST` | `/timeline/parse-text` | Parse raw text → structured events |
| `POST` | `/timeline/parse-pdf` | Parse PDF resume → structured events |
| `POST` | `/timeline/submit` | Save timeline to MongoDB |
| `GET` | `/timeline/{user_id}` | Retrieve saved timeline |
| `POST` | `/simulate` | Run 1,000 Monte Carlo simulations |
| `GET` | `/simulate/{user_id}` | Retrieve saved simulation |
| `POST` | `/explain` | Generate Groq AI narrative |
| `GET` | `/explain/{user_id}` | Retrieve saved explanation |
| `POST` | `/payment/create-session` | Create Stripe Checkout session |
| `GET` | `/payment/status/{user_id}` | Check payment status |
| `POST` | `/payment/verify-session` | Verify Stripe session after redirect |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, TypeScript, TailwindCSS v3, Framer Motion, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic v2, Motor (async MongoDB) |
| Simulation | NumPy, Markov chains, 1,000-path Monte Carlo engine |
| Causal Inference | DoWhy (backdoor criterion, linear regression estimator) |
| LLM | Groq API (`openai/gpt-oss-120b` primary, `qwen/qwen3.8-27b` fallback) |
| Database | MongoDB Atlas (Motor async driver) |
| Payments | Stripe Checkout (₹99 one-time) |
| Deployment | Render (backend), Vercel (frontend) |

---

## Screenshots

*Screenshots will be added after deployment.*

---

## License

MIT
