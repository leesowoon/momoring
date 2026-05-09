export type AgeGroup = "7-9" | "10-12" | "13-15";

export interface SessionStartRequest {
  age_group: AgeGroup;
}

export interface SessionStartResponse {
  session_id: string;
  ws_url: string;
  token: string;
}

export interface RespondRequest {
  session_id: string;
  text: string;
}

export interface RespondResponse {
  text: string;
  blocked: boolean;
}

export interface FeedbackRequest {
  session_id: string;
  turn_id: string;
  rating: "up" | "down";
  reason?: string;
}

export interface SessionTurn {
  user_text: string;
  bot_text: string;
  blocked: boolean;
  created_at: string;
}

export interface SessionDetailResponse {
  session_id: string;
  age_group: string;
  started_at: string;
  turn_count: number;
  feedback_count: number;
  turns: SessionTurn[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    trace_id: string;
  };
}

export class ApiError extends Error {
  readonly code: string;
  readonly traceId: string;
  readonly status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.code = body.error.code;
    this.traceId = body.error.trace_id;
    this.status = status;
    this.name = "ApiError";
  }
}

export type WSClientMessage =
  | { type: "audio_chunk"; session_id: string; audio_base64: string; seq?: number }
  | {
      type: "end_of_utterance";
      session_id: string;
      text?: string;
      audio_base64?: string;
    }
  | { type: "resume"; session_id: string; last_seq: number };

export type WSServerMessage =
  | { type: "partial_transcript"; text: string }
  | { type: "final_transcript"; text: string }
  | { type: "bot_text"; text: string }
  | { type: "tts_ready"; audio_url: string }
  | {
      type: "error";
      error: { code: string; message: string; trace_id: string };
    };
