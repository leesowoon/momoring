from pydantic import BaseModel, Field
from typing import Literal, Optional

AgeGroup = Literal["7-9", "10-12", "13-15"]


class SessionStartRequest(BaseModel):
    age_group: AgeGroup


class SessionStartResponse(BaseModel):
    session_id: str
    ws_url: str
    token: str


class RespondRequest(BaseModel):
    session_id: str
    text: str = Field(min_length=1)


class RespondResponse(BaseModel):
    text: str
    blocked: bool = False


class TTSSpeakRequest(BaseModel):
    session_id: str
    text: str = Field(min_length=1)


class TTSSpeakResponse(BaseModel):
    audio_url: str


class SafetyCheckRequest(BaseModel):
    text: str = Field(min_length=1)


class SafetyCheckResponse(BaseModel):
    safe: bool
    reason: Optional[str] = None


class FeedbackRequest(BaseModel):
    session_id: str
    turn_id: str
    rating: Literal["up", "down"]
    reason: Optional[str] = None


class OkResponse(BaseModel):
    ok: bool


class SessionTurn(BaseModel):
    user_text: str
    bot_text: str
    blocked: bool
    created_at: str


class SessionFeedback(BaseModel):
    turn_id: str
    rating: Literal["up", "down"]
    reason: Optional[str] = None
    created_at: str


class SessionDetailResponse(BaseModel):
    session_id: str
    age_group: str
    started_at: str
    turn_count: int
    feedback_count: int
    turns: list[SessionTurn]
    feedbacks: list[SessionFeedback]
