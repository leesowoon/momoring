export interface AudioCaptureCallbacks {
  onChunk: (base64: string) => void;
  onError?: (err: Error) => void;
}

const CHUNK_INTERVAL_MS = 500;

export class AudioCapture {
  private mediaRecorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;

  constructor(private readonly callbacks: AudioCaptureCallbacks) {}

  async start(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(this.stream, { mimeType: pickMimeType() });

      recorder.ondataavailable = (event) => {
        if (event.data.size === 0) return;
        event.data
          .arrayBuffer()
          .then((buf) => this.callbacks.onChunk(arrayBufferToBase64(buf)))
          .catch((err) => this.callbacks.onError?.(err as Error));
      };

      recorder.onerror = () => {
        this.callbacks.onError?.(new Error("media_recorder_error"));
      };

      recorder.start(CHUNK_INTERVAL_MS);
      this.mediaRecorder = recorder;
    } catch (err) {
      this.callbacks.onError?.(err as Error);
      this.cleanup();
    }
  }

  stop(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    this.cleanup();
  }

  isRecording(): boolean {
    return this.mediaRecorder?.state === "recording";
  }

  private cleanup(): void {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
    this.mediaRecorder = null;
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
