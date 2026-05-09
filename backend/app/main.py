import logging
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketState

from .config import load_settings
from .errors import (
    INTERNAL_ERROR,
    INVALID_PAYLOAD,
    RESPOND_FAILED,
    SESSION_NOT_FOUND,
    STT_FAILED,
    TTS_FAILED,
    UNKNOWN_EVENT,
    make_error_payload,
    make_ws_error_payload,
)
from .schemas import (
    FeedbackRequest,
    OkResponse,
    RespondRequest,
    RespondResponse,
    SafetyCheckRequest,
    SafetyCheckResponse,
    SessionDetailResponse,
    SessionStartRequest,
    SessionStartResponse,
    TTSSpeakRequest,
    TTSSpeakResponse,
)
from .services import metrics
from .services.logging_config import configure_logging
from .services.orchestrator import STSOrchestrator
from .services.provider_factory import ProviderFactory, ProviderFactoryConfig
from .services.provider_router import LLMRouter
from .services.safety import SafetyService
from .services.session_runtime import SessionRuntimeStore
from .services.session_store import SessionStore

configure_logging()

app = FastAPI(title="Momoring MVP API", version="0.6.0")
settings = load_settings()
logger = logging.getLogger("momoring.api")

safety_service = SafetyService()
session_store = SessionStore(persist_path=settings.session_store_path)
session_runtime = SessionRuntimeStore()

factory_cfg = ProviderFactoryConfig(
    use_real_providers=settings.use_real_providers,
    openai_api_key=settings.openai_api_key,
    anthropic_api_key=settings.anthropic_api_key,
    openai_model=settings.openai_model,
    anthropic_model=settings.anthropic_model,
    openai_base_url=settings.openai_base_url,
    anthropic_base_url=settings.anthropic_base_url,
    use_real_stt=settings.use_real_stt,
    openai_stt_model=settings.openai_stt_model,
    use_real_tts=settings.use_real_tts,
    openai_tts_model=settings.openai_tts_model,
    openai_tts_voice=settings.openai_tts_voice,
    audio_output_dir=settings.audio_output_dir,
    llm_timeout_s=settings.llm_timeout_s,
    stt_timeout_s=settings.stt_timeout_s,
    tts_timeout_s=settings.tts_timeout_s,
    max_attempts=settings.max_attempts,
)

llm_router = LLMRouter(
    primary_name=settings.llm_primary,
    fallback_name=settings.llm_fallback,
    primary=ProviderFactory.build_primary_llm(factory_cfg),
    fallback=ProviderFactory.build_fallback_llm(factory_cfg),
    force_fallback=settings.force_fallback,
)

stt_provider = ProviderFactory.build_stt(factory_cfg)
tts_provider = ProviderFactory.build_tts(factory_cfg)
sts_orchestrator = STSOrchestrator(llm=llm_router, tts=tts_provider, safety=safety_service)

static_dir = Path(__file__).resolve().parent.parent / "static"
audio_dir = Path(settings.audio_output_dir)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")


def _log(event: str, level: int = logging.INFO, **fields: Any) -> None:
    logger.log(level, event, extra={"extra_fields": {"event": event, **fields}})


def _record_safety_block(source: str, category_value: str | None) -> None:
    metrics.safety_block_total.inc(
        source=source,
        category=category_value or "unknown",
    )


@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", str(uuid4()))
    code = exc.detail if isinstance(exc.detail, str) else INTERNAL_ERROR
    payload = make_error_payload(code=code, trace_id=trace_id)
    _log("http_error", level=logging.ERROR, code=code, trace_id=trace_id, status=exc.status_code)
    response = JSONResponse(status_code=exc.status_code, content=payload)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", str(uuid4()))
    payload = make_error_payload(code=INTERNAL_ERROR, trace_id=trace_id)
    logger.exception(
        "internal_error",
        extra={"extra_fields": {"event": "internal_error", "trace_id": trace_id}},
    )
    response = JSONResponse(status_code=500, content=payload)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.get("/")
def demo_page() -> dict[str, str]:
    return {"message": "Open /static/demo.html for local demo"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm": llm_router.active_model_label()}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint() -> str:
    return metrics.registry.render()


@app.get("/v1/meta/provider")
def provider_meta() -> dict[str, str | bool]:
    return {
        "llm_primary": settings.llm_primary,
        "llm_fallback": settings.llm_fallback,
        "force_fallback": settings.force_fallback,
        "active": llm_router.active_model_label(),
        "use_real_providers": settings.use_real_providers,
        "use_real_stt": settings.use_real_stt,
        "use_real_tts": settings.use_real_tts,
    }


@app.post("/v1/sts/session/start", response_model=SessionStartResponse)
def start_session(payload: SessionStartRequest, request: Request) -> SessionStartResponse:
    session_id = str(uuid4())
    token = str(uuid4())
    session_store.create(session_id=session_id, age_group=payload.age_group)

    metrics.sessions_started_total.inc()
    metrics.active_sessions.inc()
    _log(
        "session_started",
        trace_id=request.state.trace_id,
        session_id=session_id,
        age_group=payload.age_group,
    )

    return SessionStartResponse(
        session_id=session_id,
        ws_url=f"/v1/sts/stream?session_id={session_id}",
        token=token,
    )


@app.get("/v1/sts/session/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str) -> SessionDetailResponse:
    row = session_store.as_dict(session_id)
    if not row:
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)
    return SessionDetailResponse(**row)


@app.post("/v1/safety/check", response_model=SafetyCheckResponse)
def safety_check(payload: SafetyCheckRequest) -> SafetyCheckResponse:
    result = safety_service.check(payload.text)
    return SafetyCheckResponse(safe=result.safe, reason=result.reason)


@app.post("/v1/sts/respond", response_model=RespondResponse)
async def sts_respond(payload: RespondRequest, request: Request) -> RespondResponse:
    session = session_store.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)

    total_start = perf_counter()
    result = await sts_orchestrator.respond(
        payload.text,
        age_group=session.age_group,
        history=list(session.turns),
    )
    total_ms = int((perf_counter() - total_start) * 1000)

    session_store.append_turn(payload.session_id, payload.text, result.text, result.blocked)

    metrics.sts_latency_ms.observe(total_ms)
    if result.llm_ms:
        metrics.llm_latency_ms.observe(result.llm_ms)
    if result.blocked:
        _record_safety_block(
            source=result.block_source or "unknown",
            category_value=result.block_category.value if result.block_category else None,
        )

    _log(
        "respond",
        trace_id=request.state.trace_id,
        session_id=payload.session_id,
        age_group=session.age_group,
        total_ms=total_ms,
        llm_ms=result.llm_ms,
        blocked=result.blocked,
        block_source=result.block_source,
        block_category=result.block_category.value if result.block_category else None,
    )

    return RespondResponse(text=result.text, blocked=result.blocked)


@app.post("/v1/tts/speak", response_model=TTSSpeakResponse)
async def tts_speak(payload: TTSSpeakRequest) -> TTSSpeakResponse:
    tts_start = perf_counter()
    audio_url = await sts_orchestrator.tts(payload.session_id, payload.text)
    metrics.tts_latency_ms.observe(int((perf_counter() - tts_start) * 1000))
    return TTSSpeakResponse(audio_url=audio_url)


@app.post("/v1/feedback", response_model=OkResponse)
def feedback(payload: FeedbackRequest) -> OkResponse:
    if not session_store.get(payload.session_id):
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)

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
    ws_trace_id = str(uuid4())

    async def send_error(code: str) -> None:
        if websocket.client_state == WebSocketState.CONNECTED:
            _log("ws_error", level=logging.ERROR, code=code, trace_id=ws_trace_id)
            await websocket.send_json(make_ws_error_payload(code=code, trace_id=ws_trace_id))

    try:
        while True:
            try:
                payload = await websocket.receive_json()
            except Exception:
                await send_error(INVALID_PAYLOAD)
                continue

            message_type = payload.get("type")
            session_id = payload.get("session_id")

            if not session_id:
                await send_error(INVALID_PAYLOAD)
                continue

            session_record = session_store.get(session_id)
            if not session_record:
                await send_error(SESSION_NOT_FOUND)
                continue

            if message_type == "audio_chunk":
                seq = payload.get("seq")
                if isinstance(seq, int) and not session_runtime.accept_seq(session_id, seq):
                    _log(
                        "ws_chunk_dropped",
                        trace_id=ws_trace_id,
                        session_id=session_id,
                        seq=seq,
                        reason="duplicate_or_out_of_order",
                    )
                    continue

                if session_runtime.get_phase(session_id) == "speaking":
                    await websocket.send_json({"type": "barge_in"})
                    _log("ws_barge_in", trace_id=ws_trace_id, session_id=session_id)

                session_runtime.set_phase(session_id, "listening")

                audio_base64 = payload.get("audio_base64", "")
                stt_start = perf_counter()
                try:
                    transcript = await stt_provider.transcribe_chunk(audio_base64)
                except Exception:
                    metrics.sessions_failed_total.inc(stage="stt")
                    await send_error(STT_FAILED)
                    continue
                metrics.stt_latency_ms.observe(int((perf_counter() - stt_start) * 1000))
                await websocket.send_json({"type": "partial_transcript", "text": transcript})
            elif message_type == "resume":
                last_seq = payload.get("last_seq")
                if isinstance(last_seq, int):
                    session_runtime.fast_forward_seq(session_id, last_seq)
                await websocket.send_json(
                    {
                        "type": "resumed",
                        "last_seq": session_runtime.get_last_seq(session_id),
                        "phase": session_runtime.get_phase(session_id),
                    }
                )
            elif message_type == "end_of_utterance":
                session_runtime.set_phase(session_id, "thinking")
                user_text = payload.get("text", "").strip()
                if not user_text:
                    user_text = "질문을 이해했어!"
                await websocket.send_json({"type": "final_transcript", "text": user_text})

                turn_start = perf_counter()
                try:
                    result = await sts_orchestrator.respond(
                        user_text,
                        age_group=session_record.age_group,
                        history=list(session_record.turns),
                    )
                except Exception:
                    metrics.sessions_failed_total.inc(stage="respond")
                    await send_error(RESPOND_FAILED)
                    continue

                if result.llm_ms:
                    metrics.llm_latency_ms.observe(result.llm_ms)
                if result.blocked:
                    _record_safety_block(
                        source=result.block_source or "unknown",
                        category_value=result.block_category.value
                        if result.block_category
                        else None,
                    )

                session_store.append_turn(session_id, user_text, result.text, result.blocked)
                await websocket.send_json({"type": "bot_text", "text": result.text})

                tts_start = perf_counter()
                try:
                    audio_url = await sts_orchestrator.tts(session_id, result.text)
                except Exception:
                    metrics.sessions_failed_total.inc(stage="tts")
                    await send_error(TTS_FAILED)
                    continue
                tts_ms = int((perf_counter() - tts_start) * 1000)
                metrics.tts_latency_ms.observe(tts_ms)

                total_ms = int((perf_counter() - turn_start) * 1000)
                metrics.sts_latency_ms.observe(total_ms)
                _log(
                    "ws_turn",
                    trace_id=ws_trace_id,
                    session_id=session_id,
                    age_group=session_record.age_group,
                    total_ms=total_ms,
                    llm_ms=result.llm_ms,
                    tts_ms=tts_ms,
                    blocked=result.blocked,
                    block_source=result.block_source,
                    block_category=result.block_category.value
                    if result.block_category
                    else None,
                )

                session_runtime.set_phase(session_id, "speaking")
                await websocket.send_json({"type": "tts_ready", "audio_url": audio_url})
            else:
                await send_error(UNKNOWN_EVENT)
    except WebSocketDisconnect:
        return
