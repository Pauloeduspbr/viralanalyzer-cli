"""
MCP Server that proxies ViralAnalyzer API via HTTP.

Unlike the backend MCP server (which accesses DB directly),
this server works anywhere — it calls the REST API with the
user's API key from ~/.viralanalyzer/config.json.

Transports:
  - stdio: for Claude Desktop, VS Code, Cursor (default)
  - sse: HTTP server for network access

Usage:
  viral mcp serve              # stdio (default)
  viral mcp serve --sse 3100   # SSE on port 3100
"""
import json
import logging

from mcp.server.fastmcp import FastMCP

from viral_cli.client import ViralClient
from viral_cli.config import load_config
from viral_cli.constants import API

logger = logging.getLogger(__name__)


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all tools."""

    mcp = FastMCP(
        "ViralAnalyzer CLI",
        instructions=(
            "ViralAnalyzer is an AI-powered competitive intelligence platform "
            "with 25 data connectors (TikTok, Instagram, YouTube, Google Maps, "
            "Mercado Livre, CNPJ, LinkedIn, Reddit, Twitter/X, and more). "
            "Use these tools to search viral content, analyze trends, discover "
            "businesses, enrich company data, manage pipelines, and get AI-generated "
            "content ideas."
        ),
    )

    def _client() -> ViralClient:
        """Create a fresh client per tool call (reads latest config)."""
        return ViralClient(config=load_config())

    # ═══════════════════════════════════════════════════════════════
    # SOCIAL MEDIA INTELLIGENCE TOOLS
    # ═══════════════════════════════════════════════════════════════

    @mcp.tool()
    def search_content(
        platform: str = "",
        content_type: str = "",
        min_viral_score: int = 0,
        limit: int = 20,
    ) -> str:
        """Search collected viral content across 25+ platforms.

        Returns content with metrics (views, likes, engagement) and
        AI analysis (viral score, sentiment, hooks, lessons).

        Args:
            platform: Filter by platform (tiktok, youtube, instagram, etc.)
            content_type: Filter by type (video, reel, post, review, etc.)
            min_viral_score: Minimum viral score 0-10
            limit: Max results (1-100)
        """
        client = _client()
        params: dict = {"limit": min(limit, 100)}
        if platform:
            params["platform"] = platform
        if content_type:
            params["content_type"] = content_type
        if min_viral_score > 0:
            params["min_viral_score"] = min_viral_score

        resp = client.get(API.CONTENT, params=params)
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def get_content_detail(content_id: int) -> str:
        """Get full details of a content item including metrics and AI analysis.

        Args:
            content_id: The content item ID
        """
        client = _client()
        resp = client.get(f"{API.CONTENT}/{content_id}")
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def get_platform_trends(platform: str, days: int = 30) -> str:
        """Get trending hashtags and metrics for a platform.

        Returns top 20 hashtags with frequency, avg views, avg engagement.

        Args:
            platform: Platform name (tiktok, youtube, instagram, twitter, etc.)
            days: Period in days (1-365, default 30)
        """
        client = _client()
        resp = client.get(f"{API.TRENDS}/{platform}", params={"days": days})
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def list_profiles(platform: str = "", active_only: bool = True) -> str:
        """List monitored social media profiles.

        Args:
            platform: Filter by platform (optional)
            active_only: Only show active profiles (default True)
        """
        client = _client()
        params: dict = {"active_only": active_only, "limit": 100}
        if platform:
            params["platform"] = platform
        resp = client.get(API.PROFILES, params=params)
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def add_profile(
        platform: str,
        username: str,
        url: str = "",
        category: str = "",
    ) -> str:
        """Add a new profile to monitor on a platform.

        Args:
            platform: Platform (tiktok, youtube, instagram, etc.)
            username: Profile username or handle
            url: Profile URL (optional)
            category: Category tag (competitor, influencer, etc.)
        """
        client = _client()
        body: dict = {"platform": platform, "username": username}
        if url:
            body["url"] = url
        if category:
            body["category"] = category
        resp = client.post(API.PROFILES, json_body=body)
        return json.dumps(resp, default=str, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════════
    # LEAD GENERATION TOOLS
    # ═══════════════════════════════════════════════════════════════

    @mcp.tool()
    def find_businesses(
        query: str = "",
        location: str = "",
        limit: int = 20,
    ) -> str:
        """Search Google Maps scraped business data.

        Args:
            query: Search query (e.g. 'restaurantes', 'academias')
            location: City/region filter
            limit: Max results (1-100)
        """
        client = _client()
        params: dict = {"limit": limit}
        if query:
            params["query"] = query
        if location:
            params["location"] = location
        resp = client.get(f"{API.CONTENT}", params={
            **params, "platform": "google_maps",
        })
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def enrich_cnpj(cnpj: str = "", company_name: str = "", limit: int = 10) -> str:
        """Look up Brazilian company data (CNPJ, razao social, CNAE, address).

        Args:
            cnpj: CNPJ number (e.g. '11.222.333/0001-44')
            company_name: Search by company name
            limit: Max results
        """
        client = _client()
        params: dict = {"limit": limit, "platform": "cnpj"}
        if cnpj:
            params["query"] = cnpj
        elif company_name:
            params["query"] = company_name
        resp = client.get(API.CONTENT, params=params)
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def get_competitor_intel(platform: str = "", limit: int = 20) -> str:
        """Get aggregated competitor intelligence data.

        Args:
            platform: Filter by platform (optional)
            limit: Max results
        """
        client = _client()
        params: dict = {"limit": limit}
        if platform:
            params["platform"] = platform
        resp = client.get("/api/v1/campaigns/competitors", params=params)
        return json.dumps(resp, default=str, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════════
    # INTELLIGENCE & OPERATIONS TOOLS
    # ═══════════════════════════════════════════════════════════════

    @mcp.tool()
    def get_dashboard_stats(days: int = 30) -> str:
        """Get aggregated KPIs across all platforms.

        Returns total content, views, engagement, viral scores,
        and per-platform breakdown.

        Args:
            days: Period in days (1-365, default 30)
        """
        client = _client()
        resp = client.get(API.DASHBOARD_STATS, params={"days": days})
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def list_ideas(
        status: str = "",
        platform: str = "",
        min_score: int = 0,
        limit: int = 20,
    ) -> str:
        """List AI-generated content ideas with lifecycle status.

        Args:
            status: Filter by status (generated, reviewed, in_production, published, discarded)
            platform: Filter by platform
            min_score: Minimum estimated score (0-10)
            limit: Max results (1-100)
        """
        client = _client()
        params: dict = {"limit": limit}
        if status:
            params["status"] = status
        if platform:
            params["platform"] = platform
        if min_score > 0:
            params["min_score"] = min_score
        resp = client.get(API.IDEAS, params=params)
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def trigger_pipeline(platform: str) -> str:
        """Trigger a data collection pipeline for a platform.

        Starts an Apify actor run to scrape fresh data.

        Args:
            platform: Platform to scrape (tiktok, youtube, instagram, google_maps, etc.) or 'all'
        """
        client = _client()
        resp = client.post(API.PIPELINE_TRIGGER, json_body={"platform": platform})
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def list_pipeline_runs(platform: str = "", limit: int = 10) -> str:
        """List recent pipeline execution history with status and item counts.

        Args:
            platform: Filter by platform (optional)
            limit: Max results (1-50)
        """
        client = _client()
        params: dict = {"limit": limit}
        if platform:
            params["platform"] = platform
        resp = client.get(API.PIPELINE_RUNS, params=params)
        return json.dumps(resp, default=str, ensure_ascii=False)

    @mcp.tool()
    def get_usage_stats() -> str:
        """Get API usage and subscription status.

        Returns calls used/remaining, active platforms, plan info,
        execution counts, and overage details.
        """
        client = _client()
        resp = client.get(API.BILLING_USAGE)
        return json.dumps(resp, default=str, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════════
    # RESOURCES
    # ═══════════════════════════════════════════════════════════════

    @mcp.resource("viralanalyzer://platforms")
    def get_platforms() -> str:
        """List all 25 supported platforms with categories."""
        platforms = {
            "social_media": ["tiktok", "instagram", "youtube", "twitter", "reddit", "linkedin", "threads", "facebook"],
            "marketplace": ["mercadolivre", "amazon_br", "ifood"],
            "business_data": ["google_maps", "cnpj", "trustpilot", "reclameaqui"],
            "advertising": ["facebook_ads", "google_ads"],
            "intelligence": ["competitor_intel", "brand_visibility", "seo_intelligence", "website_monitor"],
            "public_data": ["gov_transparency", "real_estate", "brazil_jobs", "sports_betting", "rss_news"],
            "creative": ["social_media_gen", "review_analyzer"],
        }
        return json.dumps(platforms, indent=2)

    @mcp.resource("viralanalyzer://help")
    def get_help() -> str:
        """Quick start guide for ViralAnalyzer MCP tools."""
        return json.dumps({
            "getting_started": [
                "1. Use get_dashboard_stats() to see your current data overview",
                "2. Use search_content(platform='tiktok') to find viral content",
                "3. Use get_platform_trends('youtube') to see trending hashtags",
                "4. Use list_ideas() to see AI-generated content ideas",
                "5. Use trigger_pipeline('instagram') to collect fresh data",
            ],
            "tips": [
                "All data is scoped to your account (API key from ~/.viralanalyzer/config.json)",
                "Use min_viral_score=7 to filter only high-performing content",
                "Combine find_businesses() with enrich_cnpj() for lead generation",
            ],
        }, indent=2)

    return mcp
