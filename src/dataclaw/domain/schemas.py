"""Pydantic schemas for API request/response."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── Source Material ─────────────────────────────────────────────────────────


class IngestRequest(BaseModel):
    source_uri: str = Field(..., description="数据源 URI (s3://, file://, http://)")
    name: str = Field(..., description="资产名称")
    source_type: str = Field(default="auto", description="源类型: s3, local, http, auto")
    metadata: dict[str, Any] | None = None


class SourceMaterialOut(BaseModel):
    id: str
    name: str
    source_uri: str
    source_type: str
    record_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Asset ───────────────────────────────────────────────────────────────────


class AssetOut(BaseModel):
    id: str
    name: str
    description: str | None
    asset_type: str
    status: str
    source_material_id: str | None
    created_at: datetime
    updated_at: datetime
    latest_version: int | None = None

    model_config = {"from_attributes": True}


# ─── Asset Version ───────────────────────────────────────────────────────────


class AssetVersionOut(BaseModel):
    id: str
    asset_id: str
    version_number: int
    status: str
    record_count: int | None
    storage_uri: str | None
    quality_metrics: dict[str, Any] | None
    inspection_report: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Problem Cluster ─────────────────────────────────────────────────────────


class ProblemClusterOut(BaseModel):
    id: str
    asset_version_id: str
    cluster_key: str
    label: str
    severity: str
    affected_count: int
    affected_ratio: float | None
    root_cause: str | None
    recommendation: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Execution Run ───────────────────────────────────────────────────────────


class RunRequest(BaseModel):
    asset_name: str
    strategy_id: str
    clusters: list[str] | None = None
    confirm: bool = False
    parameters: dict[str, Any] | None = None


class ExecutionRunOut(BaseModel):
    id: str
    asset_id: str
    input_version_id: str
    strategy_id: str
    status: str
    execution_plan: dict[str, Any] | None
    step_logs: list[dict[str, Any]] | None
    verification_results: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Publication ─────────────────────────────────────────────────────────────


class PublishRequest(BaseModel):
    asset_name: str
    version: int
    target: str
    publication_type: str = "draft"
    output_format: str | None = None
    replaces: str | None = None  # "asset_name:vN"
    note: str | None = None


class PublicationOut(BaseModel):
    id: str
    asset_version_id: str
    publication_type: str
    target: str
    output_uri: str | None
    output_format: str | None
    gates_passed: list[dict[str, Any]] | None
    retained_risks: list[str] | None
    note: str | None
    published_by: str | None
    published_at: datetime

    model_config = {"from_attributes": True}


# ─── Diff / Compare ─────────────────────────────────────────────────────────


class DiffRequest(BaseModel):
    asset_name: str
    version_a: int
    version_b: int


class DiffResult(BaseModel):
    asset_name: str
    version_a: int
    version_b: int
    metrics_diff: dict[str, Any]
    cluster_changes: list[dict[str, Any]]
    interpretation: str | None = None


# ─── Inspect ─────────────────────────────────────────────────────────────────


class InspectRequest(BaseModel):
    asset_name: str
    version: int | None = None  # None = latest
    focus: str | None = None  # "failures", "rewards", etc.
