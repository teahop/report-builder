"""Single restricted-data gate. Consume restricted_allowed(); do not reimplement it."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from profile import active_backend, profile, restricted_allowed

DataClass = Literal["synthetic", "restricted"]


class DataClassification(BaseModel):
    """Shared request fields. confirm_synthetic is a transitional synthetic alias."""

    confirm_synthetic: bool | None = Field(
        default=None,
        description="Transitional alias for data_class=synthetic. Prefer data_class.",
    )
    data_class: DataClass | None = Field(
        default=None,
        description=(
            "synthetic is always allowed; restricted only when the production "
            "Bastion profile is active."
        ),
    )
    case_id: str | None = Field(
        default=None,
        description="Optional case id; used as the Langfuse session so delete-on-finish can find traces.",
    )


def resolve_data_class(
    data_class: str | None,
    confirm_synthetic: bool | None = None,
) -> DataClass:
    if data_class == "synthetic" or data_class == "restricted":
        return data_class
    if data_class:
        return "restricted"
    if confirm_synthetic is True:
        return "synthetic"
    return "restricted"


def refusal_detail() -> str:
    reasons: list[str] = []
    if profile() != "production":
        reasons.append("profile is not production")
    if active_backend() != "bastion":
        reasons.append("backend is not Bastion")
    if not reasons:
        reasons.append("restricted data is not permitted")
    return "Restricted data refused: " + "; ".join(reasons) + "."


def assert_data_permitted(
    *,
    data_class: str | None = None,
    confirm_synthetic: bool | None = None,
) -> None:
    if resolve_data_class(data_class, confirm_synthetic) == "synthetic":
        return
    if restricted_allowed():
        return
    raise HTTPException(status_code=403, detail=refusal_detail())


def assert_request_permitted(body: Any) -> None:
    assert_data_permitted(
        data_class=getattr(body, "data_class", None),
        confirm_synthetic=getattr(body, "confirm_synthetic", None),
    )
