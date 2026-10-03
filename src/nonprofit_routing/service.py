from __future__ import annotations

import os
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .receipt_sender import (
    RoutingPreferenceRequest,
    RoutingPreferenceResult,
    apply_routing_preference,
)

app = FastAPI(title="Nonprofit capability routing")


async def get_infrai_client() -> AsyncIterator[InfraiClient]:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")
    client = InfraiClient(api_key)
    try:
        yield client
    finally:
        await client.close()


@app.put("/routing-preferences", response_model=RoutingPreferenceResult)
async def put_routing_preference(
    request: RoutingPreferenceRequest,
    client: InfraiClient = Depends(get_infrai_client),
) -> RoutingPreferenceResult:
    try:
        return await apply_routing_preference(request, client)
    except InfraiError as error:
        client_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": error.code, "message": str(error)},
        ) from error

