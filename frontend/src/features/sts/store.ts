import { create } from "zustand";

export type Phase = "idle" | "listening" | "thinking" | "speaking" | "error";

export interface ChatMessage {
  role: "user" | "bot";
  text: string;
  blocked?: boolean;
}

interface STSState {
  sessionId: string | null;
  phase: Phase;
  partialTranscript: string;
  messages: ChatMessage[];
  ttsAudioUrl: string | null;
  errorMessage: string | null;

  setSessionId: (id: string | null) => void;
  setPhase: (phase: Phase) => void;
  setPartialTranscript: (text: string) => void;
  addUserMessage: (text: string) => void;
  addBotMessage: (text: string, blocked?: boolean) => void;
  setTtsAudioUrl: (url: string | null) => void;
  setError: (msg: string | null) => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  phase: "idle" as Phase,
  partialTranscript: "",
  messages: [] as ChatMessage[],
  ttsAudioUrl: null,
  errorMessage: null,
};

export const useSTSStore = create<STSState>((set) => ({
  ...initialState,
  setSessionId: (id) => set({ sessionId: id }),
  setPhase: (phase) => set({ phase }),
  setPartialTranscript: (text) => set({ partialTranscript: text }),
  addUserMessage: (text) =>
    set((state) => ({
      messages: [...state.messages, { role: "user", text }],
      partialTranscript: "",
    })),
  addBotMessage: (text, blocked) =>
    set((state) => ({
      messages: [...state.messages, { role: "bot", text, blocked }],
    })),
  setTtsAudioUrl: (url) => set({ ttsAudioUrl: url }),
  setError: (msg) =>
    set({ errorMessage: msg, phase: msg ? "error" : "idle" }),
  reset: () => set({ ...initialState }),
}));
