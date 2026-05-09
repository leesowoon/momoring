"use client";

import { useCallback, useEffect, useRef } from "react";

import { api } from "@/lib/api/client";
import type { AgeGroup } from "@/lib/api/types";
import { ApiError } from "@/lib/api/types";
import { STSWebSocket, buildWsUrl } from "@/lib/ws/client";

import { AudioCapture } from "./audio-capture";
import { useSTSStore } from "./store";

export interface UseSTSController {
  start: (ageGroup: AgeGroup) => Promise<void>;
  beginUtterance: () => Promise<void>;
  endUtterance: () => Promise<void>;
  stop: () => void;
}

export function useSTSController(): UseSTSController {
  const wsRef = useRef<STSWebSocket | null>(null);
  const captureRef = useRef<AudioCapture | null>(null);

  const setSessionId = useSTSStore((s) => s.setSessionId);
  const setPhase = useSTSStore((s) => s.setPhase);
  const setPartialTranscript = useSTSStore((s) => s.setPartialTranscript);
  const addUserMessage = useSTSStore((s) => s.addUserMessage);
  const addBotMessage = useSTSStore((s) => s.addBotMessage);
  const setTtsAudioUrl = useSTSStore((s) => s.setTtsAudioUrl);
  const setError = useSTSStore((s) => s.setError);
  const reset = useSTSStore((s) => s.reset);

  const stop = useCallback(() => {
    captureRef.current?.stopAndCollect();
    captureRef.current = null;
    wsRef.current?.close();
    wsRef.current = null;
    reset();
  }, [reset]);

  useEffect(() => stop, [stop]);

  const start = useCallback(
    async (ageGroup: AgeGroup) => {
      try {
        setError(null);
        const session = await api.startSession({ age_group: ageGroup });
        setSessionId(session.session_id);

        const ws = new STSWebSocket({ url: buildWsUrl(session.ws_url) });
        wsRef.current = ws;

        ws.onMessage((msg) => {
          switch (msg.type) {
            case "partial_transcript":
              setPartialTranscript(msg.text);
              break;
            case "final_transcript":
              addUserMessage(msg.text);
              setPhase("thinking");
              break;
            case "bot_text":
              addBotMessage(msg.text);
              setPhase("speaking");
              break;
            case "tts_ready":
              setTtsAudioUrl(msg.audio_url);
              break;
            case "error":
              setError(`${msg.error.code}: ${msg.error.message}`);
              break;
          }
        });

        ws.connect();
        setPhase("idle");
      } catch (err) {
        const msg =
          err instanceof ApiError
            ? `${err.code}: ${err.message}`
            : (err as Error).message;
        setError(msg);
      }
    },
    [
      addBotMessage,
      addUserMessage,
      setError,
      setPartialTranscript,
      setPhase,
      setSessionId,
      setTtsAudioUrl,
    ],
  );

  const beginUtterance = useCallback(async () => {
    const ws = wsRef.current;
    const sessionId = useSTSStore.getState().sessionId;
    if (!ws || !sessionId) {
      setError("not_started: 먼저 세션을 시작해줘.");
      return;
    }

    setPhase("listening");
    const capture = new AudioCapture({
      onError: (err) => setError(`mic_error: ${err.message}`),
    });
    captureRef.current = capture;
    await capture.start();
  }, [setError, setPhase]);

  const endUtterance = useCallback(async () => {
    const ws = wsRef.current;
    const sessionId = useSTSStore.getState().sessionId;

    let audio_base64 = "";
    if (captureRef.current) {
      audio_base64 = await captureRef.current.stopAndCollect();
      captureRef.current = null;
    }

    if (ws && sessionId) {
      try {
        ws.send({
          type: "end_of_utterance",
          session_id: sessionId,
          audio_base64: audio_base64 || undefined,
        });
      } catch {
        /* ignore */
      }
    }
    setPhase("thinking");
  }, [setPhase]);

  return { start, beginUtterance, endUtterance, stop };
}
