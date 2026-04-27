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

    use_real_stt: bool = False
    openai_stt_model: str = "whisper-1"

    use_real_tts: bool = False
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    audio_output_dir: str = ".data/audio"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() == "true"


def load_settings() -> Settings:
    return Settings(
        llm_primary=os.getenv("LLM_PRIMARY", "gpt-5.4"),
        llm_fallback=os.getenv("LLM_FALLBACK", "claude"),
        force_fallback=_env_bool("FORCE_LLM_FALLBACK", False),
        session_store_path=os.getenv("SESSION_STORE_PATH", ".data/sessions.json"),
        use_real_providers=_env_bool("USE_REAL_PROVIDERS", False),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        use_real_stt=_env_bool("USE_REAL_STT", False),
        openai_stt_model=os.getenv("OPENAI_STT_MODEL", "whisper-1"),
        use_real_tts=_env_bool("USE_REAL_TTS", False),
        openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        openai_tts_voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
        audio_output_dir=os.getenv("AUDIO_OUTPUT_DIR", ".data/audio"),
    )
