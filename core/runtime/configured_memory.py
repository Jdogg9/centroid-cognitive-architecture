from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.agent_config import MemoryPolicy
from core.memory import Event, MemoryStore

SENSITIVE_METADATA_KEYS = {"customer_id", "contact_email", "api_key", "token"}


@dataclass(frozen=True)
class MemoryRetentionResult:
    retention_mode: str
    retained_events: list[Event]
    redacted_fields: list[str]
    primary_record: str


class ConfiguredMemoryManager:
    def __init__(self, policy: MemoryPolicy):
        self.policy = policy

    def retain(self, events: list[Event]) -> MemoryRetentionResult:
        retained = self._filter(events)
        redacted_fields: list[str] = []
        sanitized: list[Event] = []
        for event in retained:
            clean_event, event_redactions = self._sanitize_event(event)
            sanitized.append(clean_event)
            redacted_fields.extend(event_redactions)
        if self.policy.max_session_events > 0:
            sanitized = sanitized[-self.policy.max_session_events :]
        primary_record = sanitized[-1].event_type if sanitized else "none"
        return MemoryRetentionResult(
            retention_mode=self.policy.retention_mode,
            retained_events=sanitized,
            redacted_fields=sorted(set(redacted_fields)),
            primary_record=primary_record,
        )

    def persist(self, path: Path, events: list[Event]) -> MemoryRetentionResult:
        result = self.retain(events)
        store = MemoryStore(path)
        for event in result.retained_events:
            store.append(event)
        return result

    def _filter(self, events: list[Event]) -> list[Event]:
        if self.policy.retention_mode == "session_history":
            return list(events)
        if self.policy.retention_mode == "explicit_checkpoints":
            return [event for event in events if event.metadata.get("memory_kind") == "checkpoint"]
        if self.policy.retention_mode == "audit_only":
            return [event for event in events if event.metadata.get("memory_kind") == "audit"]
        if self.policy.retention_mode == "summary_only":
            if not events:
                return []
            source = events[-1]
            summary_metadata: dict[str, str] = {"memory_kind": "summary", "summary": "true"}
            if self.policy.retain_provenance and "provenance" in source.metadata:
                summary_metadata["provenance"] = source.metadata["provenance"]
            return [
                Event(
                    event_type="task_summary",
                    content=f"summary: {source.content}",
                    source=source.source,
                    metadata=summary_metadata,
                )
            ]
        raise ValueError(f"unsupported memory retention mode: {self.policy.retention_mode}")

    def _sanitize_event(self, event: Event) -> tuple[Event, list[str]]:
        metadata = dict(event.metadata)
        redacted_fields: list[str] = []
        if not self.policy.retain_provenance:
            metadata.pop("provenance", None)
        if not self.policy.retain_sensitive_data:
            for key in list(metadata):
                if key in SENSITIVE_METADATA_KEYS:
                    metadata[key] = "[redacted]"
                    redacted_fields.append(key)
        return (
            Event(
                event_type=event.event_type,
                content=event.content,
                source=event.source,
                event_id=event.event_id,
                timestamp=event.timestamp,
                metadata=metadata,
            ),
            redacted_fields,
        )
