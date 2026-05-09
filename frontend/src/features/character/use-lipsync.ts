"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

/**
 * Returns the current normalized audio amplitude (0..1) of an <audio>
 * element while it's playing, suitable for driving a mouth-scale animation.
 *
 * Uses a single AudioContext + AnalyserNode wired up the first time the
 * audio plays. createMediaElementSource() can only be called once per
 * element, so we cache the source/analyser across plays.
 */
export function useLipsync(audioRef: RefObject<HTMLAudioElement | null>): number {
  const [amplitude, setAmplitude] = useState(0);
  const rafRef = useRef<number | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const ensureGraph = (): AnalyserNode | null => {
      if (analyserRef.current) return analyserRef.current;
      try {
        const Ctx =
          window.AudioContext ??
          (window as unknown as { webkitAudioContext?: typeof AudioContext })
            .webkitAudioContext;
        if (!Ctx) return null;
        const ctx = new Ctx();
        const source = ctx.createMediaElementSource(audio);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyser.connect(ctx.destination);
        ctxRef.current = ctx;
        analyserRef.current = analyser;
        sourceRef.current = source;
        return analyser;
      } catch {
        return null;
      }
    };

    const start = () => {
      const analyser = ensureGraph();
      if (!analyser) return;
      void ctxRef.current?.resume();
      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sumSquares = 0;
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128;
          sumSquares += v * v;
        }
        const rms = Math.sqrt(sumSquares / data.length);
        setAmplitude(Math.min(1, rms * 2.5));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
    };

    const stop = () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      setAmplitude(0);
    };

    audio.addEventListener("play", start);
    audio.addEventListener("pause", stop);
    audio.addEventListener("ended", stop);

    return () => {
      audio.removeEventListener("play", start);
      audio.removeEventListener("pause", stop);
      audio.removeEventListener("ended", stop);
      stop();
    };
  }, [audioRef]);

  return amplitude;
}
