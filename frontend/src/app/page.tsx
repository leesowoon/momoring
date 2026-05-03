"use client";

import { useEffect, useRef, useState } from "react";

import { useSTSController } from "@/features/sts/use-sts-controller";
import { useSTSStore } from "@/features/sts/store";

export default function Home() {
  const controller = useSTSController();
  const phase = useSTSStore((s) => s.phase);
  const sessionId = useSTSStore((s) => s.sessionId);
  const messages = useSTSStore((s) => s.messages);
  const partial = useSTSStore((s) => s.partialTranscript);
  const ttsAudioUrl = useSTSStore((s) => s.ttsAudioUrl);
  const errorMessage = useSTSStore((s) => s.errorMessage);

  const [holding, setHolding] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!ttsAudioUrl) return;
    const audio = audioRef.current;
    if (!audio) return;
    audio.src = ttsAudioUrl;
    audio.play().catch(() => {});
  }, [ttsAudioUrl]);

  const onPressStart = async () => {
    if (!sessionId) return;
    setHolding(true);
    await controller.beginUtterance();
  };

  const onPressEnd = () => {
    if (!holding) return;
    setHolding(false);
    controller.endUtterance();
  };

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-10">
      <div className="flex w-full max-w-md flex-col items-center gap-6 text-center">
        <div className="size-32 rounded-full bg-gradient-to-br from-pink-300 to-purple-400 shadow-lg" />
        <h1 className="text-3xl font-bold tracking-tight">모모링</h1>
        <p className="text-sm text-zinc-500">상태: {phase}</p>

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

        <div className="w-full text-left">
          {partial && (
            <p className="mb-2 text-sm italic text-zinc-400">{partial}</p>
          )}
          <ul className="space-y-2">
            {messages.map((m, i) => (
              <li
                key={i}
                className={`rounded-lg px-3 py-2 text-sm ${
                  m.role === "user"
                    ? "bg-zinc-200 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"
                    : m.blocked
                      ? "bg-amber-100 text-amber-900"
                      : "bg-purple-100 text-purple-900"
                }`}
              >
                <span className="mr-2 text-xs font-semibold opacity-60">
                  {m.role === "user" ? "나" : "모모링"}
                </span>
                {m.text}
              </li>
            ))}
          </ul>
        </div>

        <audio ref={audioRef} hidden />
      </div>
    </main>
  );
}
