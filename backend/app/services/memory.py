from __future__ import annotations

from app.logging_config import get_logger

log = get_logger(__name__)


class MemoryService:
    def __init__(self, api_key: str, container_tag: str = "buddy-default"):
        self._enabled = bool(api_key)
        self._container_tag = container_tag
        self._client = None
        if self._enabled:
            from supermemory import Supermemory

            self._client = Supermemory(api_key=api_key)

    def get_memory_context(self, query: str) -> str:
        if not self._enabled or self._client is None:
            return ""
        try:
            profile = self._client.profile(
                container_tag=self._container_tag,
                q=query,
            )
            parts: list[str] = []
            if profile.profile.static:
                parts.append(
                    "User facts:\n" + "\n".join(profile.profile.static)
                )
            if profile.profile.dynamic:
                parts.append(
                    "Recent patterns:\n" + "\n".join(profile.profile.dynamic)
                )
            if profile.search_results and profile.search_results.results:
                memories = "\n".join(
                    r.get("memory", "")
                    for r in profile.search_results.results
                    if r.get("memory")
                )
                if memories:
                    parts.append("Relevant past conversations:\n" + memories)
            return "\n\n".join(parts)
        except Exception as e:
            log.warning(
                "memory_fetch_failed",
                category="memory",
                action="get_context",
                error=str(e),
            )
            return ""

    def store_conversation(self, user_msg: str, assistant_msg: str) -> None:
        if not self._enabled or self._client is None:
            return
        try:
            self._client.add(
                content=f"user: {user_msg}\nassistant: {assistant_msg}",
                container_tag=self._container_tag,
            )
        except Exception as e:
            log.warning(
                "memory_store_failed",
                category="memory",
                action="store",
                error=str(e),
            )
