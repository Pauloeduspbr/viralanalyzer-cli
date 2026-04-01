# ViralAnalyzer CLI

**Competitive intelligence from your terminal.** Analyze viral content, track trends, monitor competitors, and generate AI-powered content ideas across 25+ platforms.

[![PyPI](https://img.shields.io/pypi/v/viralanalyzer-cli)](https://pypi.org/project/viralanalyzer-cli/)
[![Python](https://img.shields.io/pypi/pyversions/viralanalyzer-cli)](https://pypi.org/project/viralanalyzer-cli/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Install

```bash
pip install viralanalyzer-cli
```

## Quick Start

```bash
# 1. Create a free account
viral auth register

# 2. Or login with your API key
viral auth login --api-key va_live_...

# 3. Start exploring
viral content list --platform youtube --limit 10
viral trends get tiktok --days 30
viral ideas summary
viral dashboard stats
viral billing usage
```

## What Can You Do?

### Content Intelligence
```bash
# Search viral content across 25+ platforms
viral content list --platform instagram --min-viral 7
viral content list --platform youtube --type video --limit 20
viral content get 405                    # Full details + AI analysis
viral content list -f json | jq '.'     # Pipe-friendly JSON output
```

### Trend Analysis
```bash
# Trending hashtags and metrics
viral trends get tiktok --days 7
viral trends get youtube --days 30
viral trends get instagram
```

### AI-Powered Ideas
```bash
# Generate content ideas from real viral data
viral ideas generate --count 5
viral ideas list --status generated --min-score 8
viral ideas update 42 --status reviewed
viral ideas summary                      # Lifecycle overview
```

### Pipeline Management
```bash
# Trigger data collection across platforms
viral pipelines trigger youtube
viral pipelines trigger google_maps
viral pipelines runs --limit 10          # Execution history
viral pipelines configs                  # View all configs
viral pipelines limits                   # Plan execution limits
```

### Profile Monitoring
```bash
# Track competitors and influencers
viral profiles add instagram @competitor
viral profiles add youtube @channelname
viral profiles list --platform instagram
viral profiles delete 42
```

### Dashboard & Billing
```bash
# Real-time KPIs
viral dashboard stats --days 7
viral dashboard tui                      # Interactive full-screen dashboard
viral dashboard tui --web --port 8180    # Web dashboard (browser)

# Plan usage and overage tracking
viral billing usage
```

### AI Model Settings
```bash
# Configure your AI engine (13 models, 5 providers)
viral ai models                          # List available models
viral ai get                             # Current preferences
viral ai set --ideas gpt-4.1-mini       # Change idea generation model
viral ai usage                           # Token usage this period
```

### Engagement Automation
```bash
# Monitor and automate social engagement
viral engage stats --days 7
viral engage actions --platform twitter
viral engage ai-reply twitter 123456 --tone helpful --dry-run
```

### Content Analysis (Local Files)
```bash
# Analyze markdown/text files for viral potential
viral analyze file ./blog-post.md
viral analyze dir ./content --min-score 6  # Batch analysis
viral analyze hook --min-score 6           # Install git pre-commit hook
```

### MCP Server (for AI Assistants)
```bash
# Use ViralAnalyzer as an MCP tool provider
viral mcp serve                          # stdio (Claude Desktop, VS Code, Cursor)
viral mcp serve --transport sse          # SSE (HTTP, for network access)
viral mcp inspect                        # List all 14 tools
```

**Claude Desktop config** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "viralanalyzer": {
      "command": "viral",
      "args": ["mcp", "serve"]
    }
  }
}
```

## Output Formats

Every command supports `--format` / `-f`:

```bash
viral content list -f table   # Rich table (default)
viral content list -f json    # JSON (pipe-friendly)
viral content list -f csv     # CSV (spreadsheet-friendly)
```

## Supported Platforms (25+)

| Category | Platforms |
|----------|-----------|
| **Social Media** | TikTok, Instagram, YouTube, Twitter/X, Reddit, LinkedIn, Threads, Facebook |
| **Marketplace** | Mercado Livre, Amazon BR, iFood |
| **Business Data** | Google Maps, CNPJ (Receita Federal), Trustpilot, Reclame Aqui |
| **Advertising** | Facebook Ads Library, Google Ads |
| **Intelligence** | Competitor Analysis, Brand Visibility, SEO Audit, Website Monitor |
| **Public Data** | Gov Transparency, Real Estate, Jobs, Sports Betting, RSS News |

## Apify Actors

We publish 43 data collection actors on the Apify Store. Each actor specializes in a specific platform and can be used standalone or through the ViralAnalyzer platform.

**Browse our actors:** [apify.com/viralanalyzer](https://apify.com/viralanalyzer)

Popular actors:
- [Google Maps BR Scraper](https://apify.com/viralanalyzer/google-maps-br-intelligence) - Business data + reviews
- [TikTok Viral Scanner](https://apify.com/viralanalyzer/tiktok-viral-scanner) - Viral content discovery
- [Instagram Reels Intelligence](https://apify.com/viralanalyzer/instagram-reels-intelligence) - Reels analytics
- [Mercado Livre Intelligence](https://apify.com/viralanalyzer/mercadolivre-intelligence) - Product + pricing data
- [CNPJ Enricher](https://apify.com/viralanalyzer/cnpj-enricher) - Brazilian company data (Receita Federal)
- [Reclame Aqui Scraper](https://apify.com/viralanalyzer/reclameaqui-intelligence) - Customer complaints analysis
- [YouTube Intelligence](https://apify.com/viralanalyzer/youtube-intelligence) - Video metrics + trends

## Plans

| | Starter | Business | Enterprise |
|---|---------|----------|------------|
| **Price** | R$497/mo | R$1,497/mo | R$3,997/mo |
| **API Calls** | 1,000/mo | 5,000/mo | 20,000/mo |
| **Platforms** | 5 | 10 | 25 |
| **Executions** | 30/mo | 100/mo | 500/mo |
| **AI Models** | 4 (Budget) | 8 (+ Premium) | 13 (All) |
| **MCP Server** | Local | Local | Local + SSE |

All plans include a **7-day free trial**. [Start free](https://viralanalyzer.com.br/#pricing)

## Architecture

```
viral (CLI) ──→ api.viralanalyzer.com.br (REST API)
                    │
                    ├── 25 Apify Actors (data collection)
                    ├── 5 AI Providers (Gemini, OpenAI, Grok, Anthropic, Groq)
                    ├── PostgreSQL (data storage)
                    └── Redis (caching + rate limiting)
```

The CLI is a **thin client** — all intelligence processing happens server-side. Your data stays secure.

## Privacy & Security

- All data is **encrypted in transit** (HTTPS/TLS)
- API keys stored locally in `~/.viralanalyzer/config.json` with restricted permissions (0600)
- **LGPD compliant**: download your data (`viral auth download-data`) or delete your account
- No telemetry, no tracking, no analytics in the CLI
- [Security policy](SECURITY.md)

## Requirements

- Python 3.10+
- Internet connection (API-based)
- Free account at [viralanalyzer.com.br](https://viralanalyzer.com.br)

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Built with** [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) + [Textual](https://textual.textualize.io/) + [httpx](https://www.python-httpx.org/)

**Questions?** Open an issue or reach us at [viralanalyzer.com.br](https://viralanalyzer.com.br)
