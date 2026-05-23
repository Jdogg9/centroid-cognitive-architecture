from __future__ import annotations

from core.models import create_provider_adapter
from core.models.types import ModelMessage, ModelRequest


def comparison_lines() -> list[str]:
    request = ModelRequest(
        messages=[ModelMessage(role="user", content="Compare provider capability profiles.")],
        scenario_id="project-companion",
    )
    providers = ["mock", "ollama", "vllm"]
    lines = [
        "Provider comparison: capabilities differ, Centroid policy remains authoritative.",
    ]
    for provider_id in providers:
        adapter = create_provider_adapter(provider_id, live=False)
        capabilities = adapter.capabilities()
        if provider_id == "mock":
            response = adapter.generate(request)
            text = response.text
        else:
            text = "live execution not attempted"
        lines.append(
            f"{provider_id}: responses={capabilities.responses_api} "
            f"chat_completions={capabilities.chat_completions} "
            f"tool_proposals={capabilities.tool_proposals} "
            f"provider_state={capabilities.provider_managed_conversation_state} "
            f"centroid_owns_safety=true text={text}"
        )
    return lines


def main() -> int:
    for line in comparison_lines():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
