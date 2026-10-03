from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .infrai_client import InfraiClient


class NonprofitWorkload(StrEnum):
    DONOR_RECEIPT = "donor_receipt"
    VOLUNTEER_REMINDER = "volunteer_reminder"
    CAMPAIGN_REPORT = "campaign_report"


CAPABILITY_BY_WORKLOAD: dict[NonprofitWorkload, str] = {
    NonprofitWorkload.DONOR_RECEIPT: "email.transactional",
    NonprofitWorkload.VOLUNTEER_REMINDER: "sms.transactional",
    NonprofitWorkload.CAMPAIGN_REPORT: "document.generate",
}


class RoutingPreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload: NonprofitWorkload
    excluded_provider: str | None = Field(default=None, min_length=1)


class RoutingPreferenceResult(BaseModel):
    workload: NonprofitWorkload
    capability: str
    excluded_provider: str | None
    applied: bool


async def apply_routing_preference(
    request: RoutingPreferenceRequest,
    client: InfraiClient,
) -> RoutingPreferenceResult:
    capability = CAPABILITY_BY_WORKLOAD[request.workload]
    await client.set_routing(capability, request.excluded_provider)
    return RoutingPreferenceResult(
        workload=request.workload,
        capability=capability,
        excluded_provider=request.excluded_provider,
        applied=True,
    )

