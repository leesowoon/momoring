from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    llm_primary: str = "gpt-5.4"
    llm_fallback: str = "claude"
    force_fallback: bool = False
    session_store_path: str = ".data/sessions.json"
    use_real_providers: bool = False
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_model: str = "gpt-5.4"
    anthropic_model: str = "claude-sonnet-4"
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_base_url: str = "https://api.anthropic.com/v1"


def load_settings() -> Settings:
    return Settings(
        llm_primary=os.getenv("LLM_PRIMARY", "gpt-5.4"),
        llm_fallback=os.getenv("LLM_FALLBACK", "claude"),
        force_fallback=os.getenv("FORCE_LLM_FALLBACK", "false").lower() == "true",
        session_store_path=os.getenv("SESSION_STORE_PATH", ".data/sessions.json"),
        use_real_providers=os.getenv("USE_REAL_PROVIDERS", "false").lower() == "true",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
    )
