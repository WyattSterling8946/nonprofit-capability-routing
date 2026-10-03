from __future__ import annotations

import argparse
import asyncio
import json
import os

from nonprofit_routing.infrai_client import InfraiClient
from nonprofit_routing.receipt_sender import (
    NonprofitWorkload,
    RoutingPreferenceRequest,
    apply_routing_preference,
)


async def run(workload: NonprofitWorkload, excluded_provider: str | None) -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running this script")

    client = InfraiClient(api_key)
    try:
        result = await apply_routing_preference(
            RoutingPreferenceRequest(
                workload=workload,
                excluded_provider=excluded_provider,
            ),
            client,
        )
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Set one nonprofit routing preference")
    parser.add_argument("workload", type=NonprofitWorkload, choices=list(NonprofitWorkload))
    parser.add_argument("--exclude", dest="excluded_provider")
    args = parser.parse_args()
    asyncio.run(run(args.workload, args.excluded_provider))


if __name__ == "__main__":
    main()

