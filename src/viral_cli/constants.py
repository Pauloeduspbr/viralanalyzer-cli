"""Central registry of API paths and app constants."""

APP_NAME = "viral-analyzer-cli"
APP_VERSION = "0.1.0"
DEFAULT_API_URL = "https://api.viralanalyzer.com.br"
CONFIG_DIR_NAME = ".viralanalyzer"
CONFIG_FILE_NAME = "config.json"


class API:
    """All API v1 paths used by the CLI."""

    AUTH_REGISTER = "/api/v1/billing/register"
    AUTH_LOGIN = "/api/v1/auth/login"
    AUTH_ME = "/api/v1/auth/me"
    AUTH_REFRESH = "/api/v1/auth/refresh"

    CONTENT = "/api/v1/content"
    IDEAS = "/api/v1/ideas"
    IDEAS_GENERATE = "/api/v1/ideas/generate"
    IDEAS_LIFECYCLE = "/api/v1/ideas/lifecycle/summary"

    TRENDS = "/api/v1/trends"
    PROFILES = "/api/v1/profiles"

    DASHBOARD_STATS = "/api/v1/dashboard/stats"
    DASHBOARD_HISTORY = "/api/v1/dashboard/history"

    BILLING_USAGE = "/api/v1/billing/usage"

    AI_SETTINGS = "/api/v1/ai-settings"
    AI_SETTINGS_USAGE = "/api/v1/ai-settings/usage"
    AI_SETTINGS_MODELS = "/api/v1/ai-settings/models"

    PIPELINE_TRIGGER = "/api/v1/pipelines/trigger"
    PIPELINE_RUNS = "/api/v1/pipelines/runs"
    PIPELINE_CONFIGS = "/api/v1/pipeline-configs"
