# Newsletter IA Bolsa

Live site: https://mello-lucas26ds.github.io/newsletter-ia-bolsa/

An autonomous agent that runs twice daily on GitHub Actions, fetches financial and AI news from 19 trusted sources, processes each article through an LLM pipeline for summarization and sentiment classification, and publishes the results to a static site with 49+ consecutive days of uninterrupted operation.

## How it works

The agent runs on a cron schedule (06:00 and 23:00 UTC-4, 7 days a week) with no server, no manual intervention, and no single point of human dependency.

```
GitHub Actions (cron trigger)
       |
       v
app/services/pipeline.py          -- orchestrates the full run
       |
       v
ingest.py                        -- Tavily API: 6 domain-specific queries
       |                               across 19 trusted sources
       v
dedup.py                        -- URL dedup via MD5 hash
       |                               7-day sliding window cleanup
       v
process_ai.py                    -- LangChain LCEL chain:
       |                               ChatPromptTemplate | ChatGroq | StrOutputParser
       |
       +--- [LLM succeeds] ----->  Structured output:
       |                               RESUMO, SENTIMENTO, TAGS, SCORE (0-10)
       |
       +--- [LLM fails] ------->  RegexFallbackSummarizer:
       |                               keyword-based extraction, zero cost
       v
newsletter.py                    -- formats JSON + Markdown output
       |
       v
generate_site.py                 -- Jinja2 -> static index.html
       |
       v
git commit + push               -- GitHub Pages updated
```

## Reliability design

The system is built around the assumption that external services will fail. Each failure mode has a defined fallback path:

| Failure | Fallback | Cost |
|---------|----------|------|
| Groq API unavailable at startup | RegexFallbackSummarizer activates for all articles | Zero |
| Single article fails during LLM call | Only that article falls back to regex; others continue normally | Zero for failed article |
| Tavily `topic="news"` returns errors | Retry with `topic="general"` | Same |
| No daily snapshots exist for site generation | Loads from `news_processed.json` accumulated file | N/A |
| Missing API keys in production | Pipeline refuses to start (frozen dataclass validation) | N/A |

Additional guardrails:

- **Score clamping**: output scores are clamped to 0.0-10.0 regardless of LLM output
- **Sentiment validation**: only `bullish`, `bearish`, or `neutral` accepted; anything else is rejected
- **Rate limiting**: 0.3s delay between LLM calls, 0.5s between Tavily calls
- **Max articles per run**: configurable, clamped to 1-50
- **XSS prevention**: all user-facing HTML is sanitized with bleach
- **API key safety**: config-check endpoint returns boolean status only, never exposes keys

## Observability

- **Langfuse**: optional LLM tracing per article (wrap each `resumir()` call in a trace)
- **Pipeline stats**: each run returns `{"buscadas": N, "novas": N, "processadas": N, "erros": N}`
- **Health check**: `GET /api/health` returns status and version
- **Data badge**: the live site displays whether data is real (Tavily + Groq) or demo

## Tech stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Pipeline | Python 3.12 | Orchestration, processing, dedup, formatting |
| News retrieval | Tavily API | `search_depth=advanced`, domain whitelist |
| LLM | Groq (LLaMA 3.1 8B Instant) | Fast inference, low cost |
| LLM orchestration | LangChain LCEL | `prompt \| llm \| StrOutputParser` |
| Fallback | Python regex | Zero-cost, zero-dependency |
| Deduplication | MD5 hash + JSON file | 7-day sliding window |
| Observability | Langfuse (optional) | Per-call LLM tracing |
| Templates | Jinja2 | Static site generation |
| Dev server | Flask | Local development with fake data |
| Frontend | HTML5 + CSS3 + Vanilla JS | No framework, no build step |
| Hosting | GitHub Pages | Free, serverless |
| CI/CD | GitHub Actions | Cron schedule, auto-commit |
| Testing | pytest | 14 automated tests |
| Config | Frozen dataclass + `.env` | Immutable at runtime |

## Repository structure

```
newsletter-ia-bolsa/
├── .github/
│   └── workflows/
│       └── newsletter.yml          # Cron schedule (2x/day, 7 days/week)
├── app/
│   ├── __init__.py                 # Flask factory
│   ├── routes.py                   # Dev routes + health/config APIs
│   ├── services/
│   │   ├── pipeline.py             # Main orchestrator (5-stage pipeline)
│   │   ├── ingest.py               # TavilySource (news fetching)
│   │   ├── process_ai.py           # GroqSummarizer + RegexFallbackSummarizer
│   │   ├── dedup.py                # JsonDeduplicador (URL + hash dedup)
│   │   ├── newsletter.py           # NewsletterFormatter (JSON, Markdown)
│   │   └── generate_site.py        # Static site generator (Jinja2)
│   ├── static/css/
│   │   └── style.css               # Site styles
│   └── templates/
│       ├── base.html               # Base layout
│       ├── index.html              # Main template (Flask + static)
│       ├── newsletter.html         # Per-date newsletter page
│       └── dev/
│           └── panel.html          # Dev dashboard
├── data/
│   ├── news_processed.json         # Permanent accumulated database
│   ├── news_processed_YYYY-MM-DD.json  # Daily snapshot
│   ├── newsletter_YYYY-MM-DD.md       # Daily Markdown edition
│   └── url_history.json           # Dedup history
├── tests/
│   ├── test_config.py              # Config validation (6 tests)
│   ├── test_routes.py              # Route + API tests (8 tests)
│   └── testar_integracao.py        # Integration simulation
├── config.py                       # Frozen dataclass config
├── config_editor.py                # CLI config editor
├── run.py                          # Flask dev entry point
├── requirements.txt                # Dependencies
├── .env.example                    # Environment template
└── index.html                      # Generated static site (GitHub Pages)
```

## Monitored sources

| Category | Sources |
|----------|---------|
| Financial news | Bloomberg, Reuters, Financial Times, Wall Street Journal, CNBC, MarketWatch, Investing.com, Benzinga |
| Technology | The Verge, TechCrunch, Ars Technica |
| Brazilian market | Valor Economico, InfoMoney, Money Times |

Sources are fetched via Tavily API with `search_depth=advanced` and a domain whitelist filter.

## Setup

### 1. Add GitHub Secrets

Go to Settings > Secrets > Actions and add:

| Secret | Source | Required |
|--------|--------|----------|
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | Yes |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Yes |
| `LANGFUSE_SECRET_KEY` | [langfuse.com](https://langfuse.com) | Yes |
| `LANGFUSE_PUBLIC_KEY` | [langfuse.com](https://langfuse.com) | Yes |

Without `GROQ_API_KEY`, the pipeline automatically uses the regex fallback (zero cost, lower quality).

### 2. Enable GitHub Pages

Settings > Pages > Source: branch `main`, folder `/ (root)`.

### 3. Local development

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python run.py
# http://127.0.0.1:5000
```

Flask loads real data if available; otherwise serves fake data for design preview.

### 4. Run pipeline manually

```bash
python -m app.services.pipeline
```

### 5. Run tests

```bash
python -m pytest tests/ -v
```

## Architecture decisions

**Why cumulative data instead of daily overwrite?**
Each execution appends to a permanent JSON file instead of replacing the previous day. This allows historical search by company or tag, trend analysis over time, and a site that gets richer with every run.

**Why Groq instead of GPT-4 or Claude?**
Inference speed (edge-located, no queue), significantly lower token cost, and a built-in regex fallback that guarantees the pipeline works even without an LLM provider.

**Why a static site instead of a web app?**
GitHub Pages is free, requires no server maintenance, and serves the use case: users read news, filter by sentiment, and search. No user accounts, no database writes at runtime.

**Why sentiment classification?**
Tagging each article as Bullish/Bearish/Neutral lets readers filter for what matters to their investment thesis -- something generic aggregators don't provide.

## License

MIT
