import {
  ApiError,
  type ApiErrorBody,
  type FeedbackRequest,
  type RespondRequest,
  type RespondResponse,
  type SessionDetailResponse,
  type SessionStartRequest,
  type SessionStartResponse,
} from "./types";

async function request<T>(
  path: string,
  init?: RequestInit & { json?: unknown },
): Promise<T> {
  const { json, headers, ...rest } = init ?? {};
  const res = await fetch(path, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(headers ?? {}),
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      body = {
        error: {
          code: "unknown_error",
          message: `HTTP ${res.status}`,
          trace_id: res.headers.get("X-Trace-Id") ?? "",
        },
      };
    }
    throw new ApiError(res.status, body);
  }

  return res.json() as Promise<T>;
}

export const api = {
  startSession(payload: SessionStartRequest): Promise<SessionStartResponse> {
    return request("/v1/sts/session/start", { method: "POST", json: payload });
  },

  getSession(sessionId: string): Promise<SessionDetailResponse> {
    return request(`/v1/sts/session/${encodeURIComponent(sessionId)}`);
  },

  respond(payload: RespondRequest): Promise<RespondResponse> {
    return request("/v1/sts/respond", { method: "POST", json: payload });
  },

  feedback(payload: FeedbackRequest): Promise<{ ok: boolean }> {
    return request("/v1/feedback", { method: "POST", json: payload });
  },
};
