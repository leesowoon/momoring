import { create } from "zustand";

export type Phase = "idle" | "listening" | "thinking" | "speaking" | "error";

export type FeedbackRating = "up" | "down";

export interface ChatMessage {
  role: "user" | "bot";
  text: string;
  blocked?: boolean;
  turnId?: string;
}

interface STSState {
  sessionId: string | null;
  phase: Phase;
  partialTranscript: string;
  messages: ChatMessage[];
  feedbackByTurn: Record<string, FeedbackRating>;
  ttsAudioUrl: string | null;
  errorMessage: string | null;

  setSessionId: (id: string | null) => void;
  setPhase: (phase: Phase) => void;
  setPartialTranscript: (text: string) => void;
  addUserMessage: (text: string) => void;
  addBotMessage: (text: string, blocked?: boolean) => void;
  setTtsAudioUrl: (url: string | null) => void;
  setError: (msg: string | null) => void;
  markFeedback: (turnId: string, rating: FeedbackRating) => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  phase: "idle" as Phase,
  partialTranscript: "",
  messages: [] as ChatMessage[],
  feedbackByTurn: {} as Record<string, FeedbackRating>,
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
    set((state) => {
      const turnIndex = state.messages.filter((m) => m.role === "bot").length;
      return {
        messages: [
          ...state.messages,
          { role: "bot", text, blocked, turnId: `turn-${turnIndex}` },
        ],
      };
    }),
  setTtsAudioUrl: (url) => set({ ttsAudioUrl: url }),
  setError: (msg) =>
    set({ errorMessage: msg, phase: msg ? "error" : "idle" }),
  markFeedback: (turnId, rating) =>
    set((state) => ({
      feedbackByTurn: { ...state.feedbackByTurn, [turnId]: rating },
    })),
  reset: () => set({ ...initialState }),
}));
