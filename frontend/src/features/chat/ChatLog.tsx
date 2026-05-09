"use client";

import { useEffect, useRef } from "react";

import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/types";

import type { ChatMessage, FeedbackRating } from "@/features/sts/store";
import { useSTSStore } from "@/features/sts/store";

export function ChatLog() {
  const messages = useSTSStore((s) => s.messages);
  const partial = useSTSStore((s) => s.partialTranscript);
  const feedbackByTurn = useSTSStore((s) => s.feedbackByTurn);
  const sessionId = useSTSStore((s) => s.sessionId);
  const markFeedback = useSTSStore((s) => s.markFeedback);
  const setError = useSTSStore((s) => s.setError);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, partial]);

  const submitFeedback = async (turnId: string, rating: FeedbackRating) => {
    if (!sessionId) return;
    if (feedbackByTurn[turnId]) return;

    markFeedback(turnId, rating);
    try {
      await api.feedback({
        session_id: sessionId,
        turn_id: turnId,
        rating,
      });
    } catch (err) {
      const msg =
        err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setError(`feedback_failed: ${msg}`);
    }
  };

  return (
    <div className="flex w-full flex-col gap-2">
      <div
        className="max-h-80 w-full overflow-y-auto rounded-lg border border-zinc-200 bg-white/40 p-3 text-left dark:border-zinc-800 dark:bg-zinc-900/40"
        role="log"
        aria-live="polite"
      >
        {messages.length === 0 && !partial ? (
          <p className="text-sm text-zinc-400">대화를 시작하면 여기에 표시됩니다.</p>
        ) : (
          <ul className="space-y-2">
            {messages.map((m, i) => (
              <Message
                key={i}
                message={m}
                rating={m.turnId ? feedbackByTurn[m.turnId] : undefined}
                onRate={submitFeedback}
              />
            ))}
            {partial && (
              <li className="rounded-lg px-3 py-2 text-sm italic text-zinc-400">
                …{partial}
              </li>
            )}
          </ul>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function Message({
  message,
  rating,
  onRate,
}: {
  message: ChatMessage;
  rating: FeedbackRating | undefined;
  onRate: (turnId: string, rating: FeedbackRating) => void;
}) {
  const wrapper =
    message.role === "user"
      ? "bg-zinc-200 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"
      : message.blocked
        ? "bg-amber-100 text-amber-900"
        : "bg-purple-100 text-purple-900";

  return (
    <li className={`rounded-lg px-3 py-2 text-sm ${wrapper}`}>
      <div className="flex items-baseline gap-2">
        <span className="text-xs font-semibold opacity-60">
          {message.role === "user" ? "나" : "모모링"}
        </span>
        <span className="flex-1">{message.text}</span>
      </div>

      {message.role === "bot" && message.turnId && (
        <div className="mt-2 flex items-center gap-2">
          <RateButton
            label="👍"
            active={rating === "up"}
            disabled={rating !== undefined}
            onClick={() => onRate(message.turnId!, "up")}
          />
          <RateButton
            label="👎"
            active={rating === "down"}
            disabled={rating !== undefined}
            onClick={() => onRate(message.turnId!, "down")}
          />
          {rating && (
            <span className="text-xs text-zinc-500">의견 보내줘서 고마워!</span>
          )}
        </div>
      )}
    </li>
  );
}

function RateButton({
  label,
  active,
  disabled,
  onClick,
}: {
  label: string;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex h-7 w-9 items-center justify-center rounded-full border text-sm transition ${
        active
          ? "border-purple-500 bg-purple-500 text-white"
          : "border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-100 disabled:opacity-50"
      }`}
      aria-pressed={active}
    >
      {label}
    </button>
  );
}
