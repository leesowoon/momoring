"use client";

import { useSTSStore } from "@/features/sts/store";
import type { Phase } from "@/features/sts/store";

const phaseLabels: Record<Phase, string> = {
  idle: "대기 중",
  listening: "듣는 중",
  thinking: "생각 중",
  speaking: "말하는 중",
  error: "오류",
};

const ringByPhase: Record<Phase, string> = {
  idle: "ring-0",
  listening: "ring-8 ring-pink-400/60 animate-pulse",
  thinking: "ring-4 ring-purple-300/70",
  speaking: "ring-8 ring-purple-500/70",
  error: "ring-8 ring-red-400/80 animate-[momoring-shake_0.4s_ease-in-out_3]",
};

const moodByPhase: Record<Phase, string> = {
  idle: "from-pink-200 to-purple-300",
  listening: "from-pink-300 to-pink-500",
  thinking: "from-indigo-300 to-purple-400",
  speaking: "from-purple-300 to-fuchsia-500",
  error: "from-red-300 to-red-500",
};

export function Character({ mouthAmplitude = 0 }: { mouthAmplitude?: number } = {}) {
  const phase = useSTSStore((s) => s.phase);

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`relative size-40 rounded-full bg-gradient-to-br shadow-xl transition-all duration-300 ${moodByPhase[phase]} ${ringByPhase[phase]}`}
        role="img"
        aria-label={`모모링 ${phaseLabels[phase]}`}
      >
        <Eyes phase={phase} />
        <Mouth phase={phase} amplitude={mouthAmplitude} />
        {phase === "thinking" && <ThinkingDots />}
      </div>
      <span className="text-sm text-zinc-500">{phaseLabels[phase]}</span>
    </div>
  );
}

function Eyes({ phase }: { phase: Phase }) {
  const closed = phase === "thinking";
  return (
    <div className="absolute left-1/2 top-[38%] flex w-20 -translate-x-1/2 justify-between">
      <Eye closed={closed} />
      <Eye closed={closed} />
    </div>
  );
}

function Eye({ closed }: { closed: boolean }) {
  return (
    <span
      className={`block bg-zinc-900 transition-all ${
        closed ? "h-1 w-3 rounded-full" : "h-3 w-3 rounded-full"
      }`}
    />
  );
}

function Mouth({ phase, amplitude }: { phase: Phase; amplitude: number }) {
  const baseClass = "absolute left-1/2 top-[62%] rounded-full bg-zinc-900";

  if (phase === "speaking") {
    const scaleY = Math.max(0.15, Math.min(1.6, amplitude * 5));
    return (
      <span
        className={`${baseClass} h-3 w-8`}
        style={{
          transform: `translateX(-50%) scaleY(${scaleY})`,
          transformOrigin: "center",
          transition: "transform 50ms linear",
        }}
      />
    );
  }

  const stillBase = `${baseClass} -translate-x-1/2 transition-all`;
  switch (phase) {
    case "listening":
      return <span className={`${stillBase} h-1 w-6`} />;
    case "thinking":
      return <span className={`${stillBase} h-1 w-4 opacity-50`} />;
    case "error":
      return <span className={`${stillBase} h-1.5 w-6 rotate-180`} />;
    default:
      return <span className={`${stillBase} h-1.5 w-6`} />;
  }
}

function ThinkingDots() {
  return (
    <div className="absolute -right-2 -top-2 flex gap-1 rounded-full bg-white/90 px-2 py-1 shadow">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="size-1.5 animate-bounce rounded-full bg-purple-500"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  );
}
