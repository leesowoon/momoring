"use client";

import { useEffect, useRef, useState } from "react";

import { Character } from "@/features/character/Character";
import { useLipsync } from "@/features/character/use-lipsync";
import { ChatLog } from "@/features/chat/ChatLog";
import { useSTSController } from "@/features/sts/use-sts-controller";
import { useSTSStore } from "@/features/sts/store";

export default function Home() {
  const controller = useSTSController();
  const sessionId = useSTSStore((s) => s.sessionId);
  const ttsAudioUrl = useSTSStore((s) => s.ttsAudioUrl);
  const errorMessage = useSTSStore((s) => s.errorMessage);
  const setPhase = useSTSStore((s) => s.setPhase);

  const [holding, setHolding] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mouthAmplitude = useLipsync(audioRef);

  useEffect(() => {
    if (!ttsAudioUrl) return;
    const audio = audioRef.current;
    if (!audio) return;
    audio.src = ttsAudioUrl;
    audio.play().catch(() => {});
  }, [ttsAudioUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onEnded = () => setPhase("idle");
    audio.addEventListener("ended", onEnded);
    return () => audio.removeEventListener("ended", onEnded);
  }, [setPhase]);

  const onPressStart = async () => {
    if (!sessionId) return;
    setHolding(true);
    await controller.beginUtterance();
  };

  const onPressEnd = () => {
    if (!holding) return;
    setHolding(false);
    void controller.endUtterance();
  };

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-10">
      <div className="flex w-full max-w-md flex-col items-center gap-6 text-center">
        <Character mouthAmplitude={mouthAmplitude} />
        <h1 className="text-3xl font-bold tracking-tight">모모링</h1>

        {!sessionId ? (
          <button
            type="button"
            onClick={() => controller.start("10-12")}
            className="inline-flex h-12 items-center justify-center rounded-full bg-zinc-900 px-8 text-base font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
          >
            세션 시작
          </button>
        ) : (
          <button
            type="button"
            onPointerDown={onPressStart}
            onPointerUp={onPressEnd}
            onPointerCancel={onPressEnd}
            onPointerLeave={onPressEnd}
            className={`inline-flex h-16 w-16 items-center justify-center rounded-full text-3xl text-white transition ${
              holding ? "scale-110 bg-red-500" : "bg-zinc-900 dark:bg-zinc-100 dark:text-zinc-900"
            }`}
            aria-label="누르고 있는 동안 녹음"
          >
            🎤
          </button>
        )}

        {errorMessage && (
          <p className="text-sm text-red-500">⚠️ {errorMessage}</p>
        )}

        <ChatLog />

        <audio ref={audioRef} hidden />
      </div>
    </main>
  );
}
