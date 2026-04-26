from uuid import uuid4
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from .adapters.mock import MockSTTProvider, MockTTSProvider
from .config import load_settings
from .schemas import (
    SessionStartRequest,
    SessionStartResponse,
    SessionDetailResponse,
    RespondRequest,
    RespondResponse,
    TTSSpeakRequest,
    TTSSpeakResponse,
    SafetyCheckRequest,
    SafetyCheckResponse,
    FeedbackRequest,
    OkResponse,
)
from .services.safety import SafetyService
from .services.orchestrator import STSOrchestrator
from .services.session_store import SessionStore
from .services.provider_router import LLMRouter
from .services.provider_factory import ProviderFactory, ProviderFactoryConfig

app = FastAPI(title="Momoring MVP API", version="0.4.0")
settings = load_settings()

safety_service = SafetyService()
session_store = SessionStore(persist_path=settings.session_store_path)
stt_provider = MockSTTProvider()

factory_cfg = ProviderFactoryConfig(
    use_real_providers=settings.use_real_providers,
    openai_api_key=settings.openai_api_key,
    anthropic_api_key=settings.anthropic_api_key,
    openai_model=settings.openai_model,
    anthropic_model=settings.anthropic_model,
    openai_base_url=settings.openai_base_url,
    anthropic_base_url=settings.anthropic_base_url,
)

llm_router = LLMRouter(
    primary_name=settings.llm_primary,
    fallback_name=settings.llm_fallback,
    primary=ProviderFactory.build_primary_llm(factory_cfg),
    fallback=ProviderFactory.build_fallback_llm(factory_cfg),
    force_fallback=settings.force_fallback,
)

tts_provider = MockTTSProvider()
sts_orchestrator = STSOrchestrator(llm=llm_router, tts=tts_provider, safety=safety_service)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm": llm_router.active_model_label()}


@app.get("/v1/meta/provider")
def provider_meta() -> dict[str, str | bool]:
    return {
        "llm_primary": settings.llm_primary,
        "llm_fallback": settings.llm_fallback,
        "force_fallback": settings.force_fallback,
        "active": llm_router.active_model_label(),
        "use_real_providers": settings.use_real_providers,
    }


@app.post("/v1/sts/session/start", response_model=SessionStartResponse)
def start_session(payload: SessionStartRequest) -> SessionStartResponse:
    session_id = str(uuid4())
    token = str(uuid4())
    session_store.create(session_id=session_id, age_group=payload.age_group)
    return SessionStartResponse(
        session_id=session_id,
        ws_url=f"/v1/sts/stream?session_id={session_id}",
        token=token,
    )


@app.get("/v1/sts/session/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str) -> SessionDetailResponse:
    row = session_store.as_dict(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="session_not_found")
    return SessionDetailResponse(**row)


@app.post("/v1/safety/check", response_model=SafetyCheckResponse)
def safety_check(payload: SafetyCheckRequest) -> SafetyCheckResponse:
    result = safety_service.check(payload.text)
    return SafetyCheckResponse(safe=result.safe, reason=result.reason)


@app.post("/v1/sts/respond", response_model=RespondResponse)
async def sts_respond(payload: RespondRequest) -> RespondResponse:
    result = await sts_orchestrator.respond(payload.text)
    session_store.append_turn(payload.session_id, payload.text, result.text, result.blocked)
    return RespondResponse(text=result.text, blocked=result.blocked)


@app.post("/v1/tts/speak", response_model=TTSSpeakResponse)
async def tts_speak(payload: TTSSpeakRequest) -> TTSSpeakResponse:
    audio_url = await sts_orchestrator.tts(payload.session_id, payload.text)
    return TTSSpeakResponse(audio_url=audio_url)


@app.post("/v1/feedback", response_model=OkResponse)
def feedback(payload: FeedbackRequest) -> OkResponse:
    session_store.append_feedback(
        session_id=payload.session_id,
        turn_id=payload.turn_id,
        rating=payload.rating,
        reason=payload.reason,
    )
    return OkResponse(ok=True)


@app.websocket("/v1/sts/stream")
async def sts_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")
            session_id = payload.get("session_id", "mock")

            if message_type == "audio_chunk":
                transcript = await stt_provider.transcribe_chunk(payload.get("audio_base64", ""))
                await websocket.send_json({"type": "partial_transcript", "text": transcript})
            elif message_type == "end_of_utterance":
                user_text = payload.get("text", "질문을 이해했어!")
                await websocket.send_json({"type": "final_transcript", "text": user_text})
                result = await sts_orchestrator.respond(user_text)
                session_store.append_turn(session_id, user_text, result.text, result.blocked)
                await websocket.send_json({"type": "bot_text", "text": result.text})
                audio_url = await sts_orchestrator.tts(session_id, result.text)
                await websocket.send_json({"type": "tts_ready", "audio_url": audio_url})
            else:
                await websocket.send_json({"type": "error", "message": "unknown event"})
    except WebSocketDisconnect:
        return
