"""Best-effort Redis coordination with a bounded in-process fallback."""

import asyncio
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any

from app.company_intelligence.schemas import CompanyIntelligenceSearchResult


@dataclass
class _ExpiringValue:
    value: str
    expires_at: float


class CompanyIntelligenceCache:
    """Store preview JSON and coordinate remote work without making Redis mandatory."""

    def __init__(
        self,
        *,
        redis: Any | None,
        ttl_seconds: int,
        rate_limit_max_requests: int,
        rate_limit_window_seconds: int,
        redis_timeout_seconds: float = 0.2,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds
        self._rate_limit_max_requests = rate_limit_max_requests
        self._rate_limit_window_seconds = rate_limit_window_seconds
        self._redis_timeout_seconds = redis_timeout_seconds
        self._memory_cache: dict[str, _ExpiringValue] = {}
        self._memory_locks: dict[str, _ExpiringValue] = {}
        self._memory_requests: dict[str, deque[float]] = {}
        self._memory_guard = asyncio.Lock()

    @staticmethod
    def _cache_key(name: str) -> str:
        return f"company-intelligence:result:{name}"

    @staticmethod
    def _lock_key(name: str) -> str:
        return f"company-intelligence:lock:{name}"

    @staticmethod
    def _rate_key(name: str) -> str:
        return f"company-intelligence:rate:{name}"

    async def get(self, normalized_name: str) -> CompanyIntelligenceSearchResult | None:
        key = self._cache_key(normalized_name)
        raw = await self._get_redis(key)
        if raw is None:
            raw = await self._get_memory(self._memory_cache, key)
        if raw is None:
            return None
        try:
            return CompanyIntelligenceSearchResult.model_validate_json(raw)
        except ValueError:
            return None

    async def set(self, normalized_name: str, result: CompanyIntelligenceSearchResult) -> None:
        key = self._cache_key(normalized_name)
        raw = result.model_dump_json()
        await self._set_memory(self._memory_cache, key, raw, self._ttl_seconds)
        await self._set_redis(key, raw, ex=self._ttl_seconds)

    async def acquire_lock(self, normalized_name: str) -> str | None:
        key = self._lock_key(normalized_name)
        token = uuid.uuid4().hex
        acquired = await self._set_redis(key, token, ex=self._ttl_seconds, nx=True)
        if acquired is not None:
            return token if acquired else None
        now = time.monotonic()
        async with self._memory_guard:
            current = self._memory_locks.get(key)
            if current is not None and current.expires_at > now:
                return None
            self._memory_locks[key] = _ExpiringValue(token, now + self._ttl_seconds)
            return token

    async def release_lock(self, normalized_name: str, token: str) -> None:
        key = self._lock_key(normalized_name)
        if self._redis is not None:
            try:
                await asyncio.wait_for(
                    self._redis.eval(
                        "if redis.call('get', KEYS[1]) == ARGV[1] then "
                        "return redis.call('del', KEYS[1]) else return 0 end",
                        1,
                        key,
                        token,
                    ),
                    timeout=self._redis_timeout_seconds,
                )
            except Exception:
                pass
        async with self._memory_guard:
            current = self._memory_locks.get(key)
            if current is not None and current.value == token:
                self._memory_locks.pop(key, None)

    async def wait_for_result(
        self, normalized_name: str, timeout_seconds: float
    ) -> CompanyIntelligenceSearchResult | None:
        deadline = time.monotonic() + max(timeout_seconds, 0)
        while time.monotonic() < deadline:
            result = await self.get(normalized_name)
            if result is not None:
                return result
            await asyncio.sleep(min(0.05, max(deadline - time.monotonic(), 0)))
        return await self.get(normalized_name)

    async def allow_request(self, normalized_name: str) -> bool:
        key = self._rate_key(normalized_name)
        if self._redis is not None:
            try:
                count = await asyncio.wait_for(
                    self._redis.incr(key), timeout=self._redis_timeout_seconds
                )
                if count == 1:
                    await asyncio.wait_for(
                        self._redis.expire(key, self._rate_limit_window_seconds),
                        timeout=self._redis_timeout_seconds,
                    )
                return count <= self._rate_limit_max_requests
            except Exception:
                pass

        now = time.monotonic()
        cutoff = now - self._rate_limit_window_seconds
        async with self._memory_guard:
            requests = self._memory_requests.setdefault(key, deque())
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self._rate_limit_max_requests:
                return False
            requests.append(now)
            return True

    async def _get_redis(self, key: str) -> str | None:
        if self._redis is None:
            return None
        try:
            value = await asyncio.wait_for(
                self._redis.get(key), timeout=self._redis_timeout_seconds
            )
        except Exception:
            return None
        return value if isinstance(value, str) else None

    async def _set_redis(self, key: str, value: str, **kwargs: object) -> bool | None:
        if self._redis is None:
            return None
        try:
            response = await asyncio.wait_for(
                self._redis.set(key, value, **kwargs), timeout=self._redis_timeout_seconds
            )
        except Exception:
            return None
        return bool(response)

    async def _get_memory(
        self, values: dict[str, _ExpiringValue], key: str
    ) -> str | None:
        now = time.monotonic()
        async with self._memory_guard:
            item = values.get(key)
            if item is None:
                return None
            if item.expires_at <= now:
                values.pop(key, None)
                return None
            return item.value

    async def _set_memory(
        self, values: dict[str, _ExpiringValue], key: str, value: str, ttl: int
    ) -> None:
        async with self._memory_guard:
            values[key] = _ExpiringValue(value, time.monotonic() + ttl)
