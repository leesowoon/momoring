from collections import defaultdict
from threading import Lock
from typing import Iterable

InfBucket = float("inf")


class Counter:
    def __init__(self, name: str, help_text: str = "") -> None:
        self.name = name
        self.help = help_text
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = Lock()

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] += amount

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} counter"
        with self._lock:
            items = list(self._values.items())
        if not items:
            yield f"{self.name} 0"
            return
        for key, value in items:
            label_str = ""
            if key:
                inner = ",".join(f'{k}="{v}"' for k, v in key)
                label_str = "{" + inner + "}"
            yield f"{self.name}{label_str} {value}"


class Histogram:
    DEFAULT_BUCKETS: tuple[float, ...] = (50, 100, 200, 500, 1000, 2000, 5000, 10000, InfBucket)

    def __init__(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] | None = None,
    ) -> None:
        self.name = name
        self.help = help_text
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: list[int] = [0] * len(self.buckets)
        self._sum = 0.0
        self._count = 0
        self._lock = Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            for i, b in enumerate(self.buckets):
                if value <= b:
                    self._counts[i] += 1
            self._sum += value
            self._count += 1

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} histogram"
        with self._lock:
            counts = list(self._counts)
            total_sum = self._sum
            total_count = self._count
        for i, b in enumerate(self.buckets):
            le = "+Inf" if b == InfBucket else str(b)
            yield f'{self.name}_bucket{{le="{le}"}} {counts[i]}'
        yield f"{self.name}_sum {total_sum}"
        yield f"{self.name}_count {total_count}"


class Gauge:
    def __init__(self, name: str, help_text: str = "") -> None:
        self.name = name
        self.help = help_text
        self._value = 0.0
        self._lock = Lock()

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value -= amount

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} gauge"
        with self._lock:
            value = self._value
        yield f"{self.name} {value}"


class MetricsRegistry:
    def __init__(self) -> None:
        self._metrics: list[Counter | Histogram | Gauge] = []

    def counter(self, name: str, help_text: str = "") -> Counter:
        m = Counter(name, help_text)
        self._metrics.append(m)
        return m

    def histogram(
        self, name: str, help_text: str = "", buckets: tuple[float, ...] | None = None
    ) -> Histogram:
        m = Histogram(name, help_text, buckets)
        self._metrics.append(m)
        return m

    def gauge(self, name: str, help_text: str = "") -> Gauge:
        m = Gauge(name, help_text)
        self._metrics.append(m)
        return m

    def render(self) -> str:
        lines: list[str] = []
        for m in self._metrics:
            lines.extend(m.render())
        return "\n".join(lines) + "\n"


registry = MetricsRegistry()

sessions_started_total = registry.counter(
    "momoring_sessions_started_total", "Total sessions started."
)
sessions_failed_total = registry.counter(
    "momoring_sessions_failed_total", "Total session-level failures."
)
sts_latency_ms = registry.histogram(
    "momoring_sts_latency_ms", "End-to-end STS turn latency in milliseconds."
)
stt_latency_ms = registry.histogram(
    "momoring_stt_latency_ms", "STT step latency in milliseconds."
)
llm_latency_ms = registry.histogram(
    "momoring_llm_latency_ms", "LLM step latency in milliseconds."
)
tts_latency_ms = registry.histogram(
    "momoring_tts_latency_ms", "TTS step latency in milliseconds."
)
active_sessions = registry.gauge("momoring_active_sessions", "Currently active sessions.")
safety_block_total = registry.counter(
    "momoring_safety_block_total", "Safety blocks by category and source."
)
