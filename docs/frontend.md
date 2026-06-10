# Frontend Guide

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

The CreditBridge frontend is a React single-page application built with Vite, styled with Tailwind CSS v4, and designed in a **neobrutalist** aesthetic — high-contrast ink-on-cream palette, bold borders, offset shadows, and Space Grotesk / DM Mono typography.

All frontend code lives under **`frontend/`** in the repository root.

---

## Directory Structure

```
frontend/
├── public/                     # Static assets (favicon, etc.)
├── src/
│   ├── main.jsx                # App entry point — Router + QueryClientProvider
│   ├── index.css               # Global design system (Tailwind @theme tokens)
│   │
│   ├── lib/
│   │   └── api.js              # Axios instance + named endpoint helpers
│   │
│   ├── pages/
│   │   ├── Landing.jsx         # Home page — two CTA cards (Lender / Applicant)
│   │   ├── LenderDashboard.jsx # Applicant table, filters, score drilldown panel
│   │   └── ApplicantView.jsx   # Self-service form, live score gauge, reason tips
│   │
│   └── components/
│       ├── ScoreGauge.jsx      # Animated SVG arc gauge (300–900 scale)
│       ├── BandBadge.jsx       # Color-coded credit band pill
│       ├── FactorCard.jsx      # Single SHAP reason card with direction bar
│       ├── WaterfallChart.jsx  # Recharts horizontal SHAP waterfall
│       ├── FairnessPanel.jsx   # Fairness flag display panel
│       └── ModelCardModal.jsx  # Overlay showing full model card metrics
│
├── index.html                  # Vite HTML entry — Google Fonts, SEO meta tags
├── vite.config.js              # Vite config — React plugin, Tailwind, API proxy
├── package.json
├── eslint.config.js
├── nginx.conf                  # Nginx config for production Docker image
└── Dockerfile                  # Multi-stage: Vite build → nginx static serving
```

---

## Running the Frontend Locally

```powershell
cd frontend
npm install          # first time only
npm run dev          # starts Vite dev server at http://localhost:5173
```

The Vite dev server proxies `/score`, `/model-card`, and `/health` requests to `http://localhost:8000` (the FastAPI backend) — so you need the backend running simultaneously.

```powershell
# Terminal 1: start backend
cd backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: start frontend
cd frontend
npm run dev
```

---

## Design System (`src/index.css`)

CreditBridge uses Tailwind CSS v4's `@theme` directive to define a centralized token set:

| Token | Value | Use |
|-------|-------|-----|
| `--color-cream` | `#F5F0E8` | Page background |
| `--color-ink` | `#0A0A0A` | Primary text, borders |
| `--color-blue` | `#0066FF` | Accent, CTAs, highlighted score |
| `--color-cream-dark` | `#EDE7D9` | Card backgrounds |
| `--shadow-brutal` | `6px 6px 0 #0A0A0A` | Neobrutalist offset shadow |

**Typography**: [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) for headings and UI labels, [DM Mono](https://fonts.google.com/specimen/DM+Mono) for numeric values and code-like content.

**Component classes** defined in `index.css`:
- `.btn-primary` — filled ink button with brutal shadow, lifts on hover
- `.btn-secondary` — outlined button with blue border
- `.card` — bordered panel with offset shadow
- `.navbar` — fixed top nav with border bottom
- `.badge` — inline status pill

---

## Pages

### `Landing.jsx`
The entry page. Displays:
- Project tagline and a brief value proposition.
- Two large CTA cards: **LENDER VIEW** and **CHECK MY SCORE**.
- A "How It Works" signal flow strip showing the 4 data sources.
- A live **Model Card Snapshot** (fetched from `GET /model-card`) showing AUC, KS, ECE, and model version.

Navigation: clicking a CTA card routes to `/lender` or `/applicant` via React Router.

### `LenderDashboard.jsx`
A simulated lender view (useful for demos without a real database of applicants). Shows:
- A searchable, filterable table of mock applicants with scores and band badges.
- Clicking a row opens a side panel with the full score breakdown — gauge, factor cards, waterfall chart, and fairness flags.
- A "Run Score" button that calls `POST /score` with the selected applicant's signals.

### `ApplicantView.jsx`
A self-service score form for end users. The form collects:
- Demographics (gender, geography, income bracket, MSME status).
- Monthly UPI transaction counts, failure counts, amounts, merchant counts.
- Utility payment status per month.
- Mobile recharge status and plan values.
- GST filing status (if MSME).

On submit it calls `POST /score` and renders the result in-page: the animated score gauge, band badge, top 3 factor cards (positive/negative), SHAP waterfall chart, and any fairness flags.

---

## Components

### `ScoreGauge.jsx`
An SVG arc gauge that animates from 0 to the applicant's score. The arc color matches the credit band (green for Prime, yellow for Subprime, red for Decline). The score number is rendered in DM Mono at the center, with the band label below.

Key props: `score` (300–900), `band` (string), `animated` (boolean).

### `BandBadge.jsx`
A pill badge color-coded per band:

| Band | Background | Text |
|------|-----------|------|
| Prime | `#00C853` | Black |
| Near-prime | `#69F0AE` | Black |
| Subprime | `#FFD740` | Black |
| High risk | `#FF6D00` | White |
| Decline | `#D50000` | White |

### `FactorCard.jsx`
Displays a single SHAP reason. A vertical color bar on the left (green = positive impact on score, red = negative) communicates direction at a glance. The card body shows the plain-language reason text and a small chip with the SHAP point value.

### `WaterfallChart.jsx`
A Recharts horizontal bar chart showing the top 8 SHAP feature contributions. Bars are colored green (score-positive) or red (score-negative). A custom tooltip shows the feature name and exact SHAP value. The chart is responsive and adapts to container width.

### `FairnessPanel.jsx`
Renders fairness flag strings returned by the API. Each flag is displayed as a warning chip. If no flags are present, the panel shows a green "No fairness concerns detected" notice.

### `ModelCardModal.jsx`
A full-screen overlay (backdrop click to dismiss) showing:
- Model name, version, framework.
- Performance metrics (AUC, KS, ECE, Brier Score) with traffic-light indicators against targets.
- Fairness audit summary with violations if any.
- A "View full OpenAPI docs" link.

---

## API Integration (`src/lib/api.js`)

```js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

export const scoreApplicant = (payload) => api.post('/score', payload).then(r => r.data)
export const getScore = (id) => api.get(`/score/${id}`).then(r => r.data)
export const getModelCard = () => api.get('/model-card').then(r => r.data)
export const getHealth = () => api.get('/health').then(r => r.data)
```

`VITE_API_BASE_URL` can be set via a `.env` file in the `frontend/` directory for production deployments. During local development, the Vite proxy handles routing.

---

## Production Build

```powershell
cd frontend
npm run build          # outputs to frontend/dist/
```

The production build is served by nginx inside the frontend Docker container. See [deployment.md](./deployment.md) for full Docker setup.
