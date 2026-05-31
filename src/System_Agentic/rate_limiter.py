import time
import threading
from enum import Enum

_lock = threading.Lock()

PROVIDER_CONFIG = {
    "gemini/gemini-2.5-flash":        {"rpm": 5,   "tpd": 1500, "priority": 1, "key_var": "GEMINI_API_KEY"},
    "gemini/gemini-3-flash-preview":  {"rpm": 30,  "tpd": 1500, "priority": 2, "key_var": "GEMINI_API_KEY"},
    "gemini/gemini-2.5-flash-lite":   {"rpm": 10,  "tpd": 20,   "priority": 3, "key_var": "GEMINI_API_KEY"},
    "groq/llama-3.3-70b-versatile":   {"rpm": 30,  "tpd": 100000, "priority": 4, "key_var": "api_key_LLM"},
    "groq/mixtral-8x7b-32768":        {"rpm": 30,  "tpd": 100000, "priority": 5, "key_var": "api_key_LLM"},
}

SORTED_MODELS = sorted(PROVIDER_CONFIG, key=lambda m: PROVIDER_CONFIG[m]["priority"])


class LimiterState(Enum):
    AVAILABLE = "AVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


class ProviderState:
    def __init__(self, name: str):
        self.name = name
        self.state = LimiterState.AVAILABLE
        self.cooldown_until = 0.0
        self.last_error = ""
        self.total_calls = 0
        self.daily_calls = 0
        self.daily_reset = time.time()
        self.minute_calls = 0
        self.minute_reset = time.time()

    def record_success(self):
        self.total_calls += 1
        self.daily_calls += 1
        self.minute_calls += 1
        self.state = LimiterState.AVAILABLE
        self.cooldown_until = 0
        self.last_error = ""

    def record_429(self, error_msg: str, retry_after: int, is_daily: bool = False):
        self.last_error = error_msg[:200]
        self.total_calls += 1
        self.daily_calls += 1
        self.minute_calls += 1

        if is_daily or retry_after >= 3600:
            self.state = LimiterState.QUOTA_EXCEEDED
            self.cooldown_until = time.time() + 86400
        else:
            self.state = LimiterState.RATE_LIMITED
            self.cooldown_until = time.time() + min(retry_after, 120)

    def can_try(self) -> bool:
        now = time.time()
        if now - self.daily_reset > 86400:
            self.daily_calls = 0
            self.daily_reset = now
            self.state = LimiterState.AVAILABLE
            self.cooldown_until = 0
        if now - self.minute_reset > 60:
            self.minute_calls = 0
            self.minute_reset = now
        if self.state == LimiterState.QUOTA_EXCEEDED:
            if now >= self.cooldown_until:
                self.state = LimiterState.AVAILABLE
                return True
            return False
        if self.state == LimiterState.RATE_LIMITED:
            if now >= self.cooldown_until:
                self.state = LimiterState.AVAILABLE
                return True
            return False
        cfg = PROVIDER_CONFIG.get(self.name)
        if cfg:
            if self.minute_calls >= cfg["rpm"]:
                return False
            if self.daily_calls >= cfg["tpd"]:
                self.state = LimiterState.QUOTA_EXCEEDED
                self.cooldown_until = now + 86400
                return False
        return True

    def remaining_daily(self) -> int:
        cfg = PROVIDER_CONFIG.get(self.name)
        return max(0, cfg["tpd"] - self.daily_calls) if cfg else 999999

    def remaining_minute(self) -> int:
        cfg = PROVIDER_CONFIG.get(self.name)
        return max(0, cfg["rpm"] - self.minute_calls) if cfg else 999999

    def state_name(self) -> str:
        return self.state.value


_global_call_counter = 0
_request_counters: dict[str, int] = {}
_request_lock = threading.Lock()


def reset_global_calls():
    global _global_call_counter
    with _request_lock:
        _global_call_counter = 0
        _request_counters.clear()


def inc_global_call(request_id: str = ""):
    global _global_call_counter
    with _request_lock:
        _global_call_counter += 1
        if request_id:
            _request_counters[request_id] = _request_counters.get(request_id, 0) + 1


def get_call_stats(request_id: str = "") -> dict:
    with _request_lock:
        return {
            "global_calls": _global_call_counter,
            "request_calls": _request_counters.get(request_id, 0) if request_id else 0,
        }


class ProviderManager:
    def __init__(self):
        self.providers: dict[str, ProviderState] = {}

    def _get(self, model: str) -> ProviderState:
        with _lock:
            if model not in self.providers:
                self.providers[model] = ProviderState(model)
            return self.providers[model]

    def get_best(self) -> str | None:
        for model in SORTED_MODELS:
            ps = self._get(model)
            if ps.can_try():
                return model
        return None

    def record_success(self, model: str):
        self._get(model).record_success()

    def record_429(self, model: str, error_msg: str, retry_after: int, is_daily: bool = False):
        self._get(model).record_429(error_msg, retry_after, is_daily)
        inc_global_call(f"429_{model}")

    def summary(self) -> dict:
        with _lock:
            return {
                name: {
                    "state": s.state_name(),
                    "calls": s.total_calls,
                    "daily": s.daily_calls,
                    "remaining_daily": s.remaining_daily(),
                    "remaining_minute": s.remaining_minute(),
                    "cooldown_remaining": max(0, s.cooldown_until - time.time()),
                    "last_error": s.last_error[:100] if s.last_error else None,
                }
                for name, s in self.providers.items()
            }

    def has_any_available(self) -> bool:
        for model in SORTED_MODELS:
            if self._get(model).can_try():
                return True
        return False

    def reset_all(self):
        with _lock:
            self.providers.clear()


_manager = ProviderManager()


def get_manager() -> ProviderManager:
    return _manager
