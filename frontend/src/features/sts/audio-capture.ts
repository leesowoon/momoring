export interface AudioCaptureCallbacks {
  onError?: (err: Error) => void;
}

export class AudioCapture {
  private mediaRecorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];
  private mimeType: string = "audio/webm";

  constructor(private readonly callbacks: AudioCaptureCallbacks = {}) {}

  async start(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mimeType = pickMimeType();
      const recorder = new MediaRecorder(this.stream, { mimeType: this.mimeType });
      this.chunks = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) this.chunks.push(event.data);
      };

      recorder.onerror = () => {
        this.callbacks.onError?.(new Error("media_recorder_error"));
      };

      recorder.start();
      this.mediaRecorder = recorder;
    } catch (err) {
      this.callbacks.onError?.(err as Error);
      this.cleanup();
    }
  }

  /** Stop recording and resolve the full utterance as base64. */
  stopAndCollect(): Promise<string> {
    return new Promise((resolve) => {
      const recorder = this.mediaRecorder;
      if (!recorder) {
        resolve("");
        return;
      }

      recorder.onstop = async () => {
        try {
          const blob = new Blob(this.chunks, { type: this.mimeType });
          const buffer = await blob.arrayBuffer();
          resolve(arrayBufferToBase64(buffer));
        } catch {
          resolve("");
        } finally {
          this.cleanup();
        }
      };

      if (recorder.state !== "inactive") {
        recorder.stop();
      } else {
        this.cleanup();
        resolve("");
      }
    });
  }

  isRecording(): boolean {
    return this.mediaRecorder?.state === "recording";
  }

  private cleanup(): void {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
    this.mediaRecorder = null;
    this.chunks = [];
  }
}

function pickMimeType(): string {
  if (typeof MediaRecorder === "undefined") return "audio/webm";
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c)) return c;
  }
  return "audio/webm";
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  let binary = "";
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}
