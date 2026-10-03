import asyncio
import json

import httpx

from nonprofit_routing.infrai_client import InfraiClient
from nonprofit_routing.receipt_sender import (
    RoutingPreferenceRequest,
    apply_routing_preference,
)


def test_volunteer_reminder_excludes_only_its_selected_provider() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        captured["authorization"] = request.headers["Authorization"]
        return httpx.Response(200, json={"ok": True, "data": {"updated": True}})

    async def scenario() -> object:
        client = InfraiClient(
            "test-key",
            transport=httpx.MockTransport(handler),
        )
        try:
            return await apply_routing_preference(
                RoutingPreferenceRequest(
                    workload="volunteer_reminder",
                    excluded_provider="vendor-sunrise",
                ),
                client,
            )
        finally:
            await client.close()

    result = asyncio.run(scenario())

    assert captured == {
        "method": "PUT",
        "path": "/v1/account/routing/set",
        "body": {
            "capability": "sms.transactional",
            "exclude": ["vendor-sunrise"],
        },
        "authorization": "Bearer test-key",
    }
    assert result.workload == "volunteer_reminder"
    assert result.capability == "sms.transactional"
    assert result.applied is True
