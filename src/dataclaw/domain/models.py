"""Dataclaw 核心领域对象模型。

6 个最小领域对象:
- SourceMaterial: 原始数据（进入 Dataclaw 的输入来源）
- Asset: 资产（长期身份，值得持续维护）
- AssetVersion: 资产版本（可比较、可验证、可发布的具体状态快照）
- ProblemCluster: 问题分组（识别出的共同质量问题或失败模式）
- ExecutionRun: 处理记录（一次具体改进动作的完整记录）
- Publication: 发布记录（带门禁、用途和说明的正式交付）
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ─── Enums ───────────────────────────────────────────────────────────────────


class AssetStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class VersionStatus(str, enum.Enum):
    raw = "raw"
    inspected = "inspected"
    processed = "processed"
    published = "published"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    aborted = "aborted"


class Severity(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class PublicationType(str, enum.Enum):
    draft = "draft"
    formal = "formal"


# ─── Models ──────────────────────────────────────────────────────────────────


class SourceMaterial(Base):
    """原始数据：进入 Dataclaw 的原始输入来源。

    回答：这批东西从哪里来。
    典型：rollout trace, failure trace, FAQ, bad case bundle, eval set
    """

    __tablename__ = "source_materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)  # s3, local, http
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # relationships
    assets: Mapped[list[Asset]] = relationship(back_populates="source_material")


class Asset(Base):
    """资产：值得长期维护、持续比较、持续发布的 AI 数据资产。

    判断标准：只要值得被长期维护，就应该是 Asset。
    """

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)  # trajectory, preference_pairs, process_rewards, sft_dataset, eval_set
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.active)
    source_material_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source_materials.id"), nullable=True
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # relationships
    source_material: Mapped[SourceMaterial | None] = relationship(back_populates="assets")
    versions: Mapped[list[AssetVersion]] = relationship(back_populates="asset", order_by="AssetVersion.version_number")


class AssetVersion(Base):
    """资产版本：某个资产在某一时刻的具体状态快照。

    真正被比较、被验证、被发布的是 AssetVersion。
    Asset 是长期身份，AssetVersion 是可比较状态。
    """

    __tablename__ = "asset_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)  # v0, v1, v2...
    status: Mapped[VersionStatus] = mapped_column(Enum(VersionStatus), default=VersionStatus.raw)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # 质量快照（合并 QualitySnapshot 到 version 元数据中）
    quality_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # 体检报告
    inspection_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 来源 run（如果是由 ExecutionRun 产生的）
    produced_by_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("execution_runs.id", use_alter=True), nullable=True
    )

    # relationships
    asset: Mapped[Asset] = relationship(back_populates="versions")
    problem_clusters: Mapped[list[ProblemCluster]] = relationship(back_populates="asset_version")
    produced_by_run: Mapped[ExecutionRun | None] = relationship(
        back_populates="output_version", foreign_keys=[produced_by_run_id]
    )


class ProblemCluster(Base):
    """问题分组：资产版本中被识别出来的共同质量问题或失败模式。

    它是体检页的核心对象、归因页的主对象、执行推荐的输入、差异比较的关键单元。
    """

    __tablename__ = "problem_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("asset_versions.id"), nullable=False
    )
    cluster_key: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. "missing_reward"
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.medium)
    affected_count: Mapped[int] = mapped_column(Integer, default=0)
    affected_ratio: Mapped[float | None] = mapped_column(nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")  # open, resolved, accepted
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # relationships
    asset_version: Mapped[AssetVersion] = relationship(back_populates="problem_clusters")


class ExecutionRun(Base):
    """处理记录：一次具体改进动作的完整记录。

    回答：这次系统到底做了什么。
    串起：输入版本、选中的问题分组、执行动作、产出版本、风险与异常、验证结果。
    """

    __tablename__ = "execution_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    input_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("asset_versions.id"), nullable=False
    )
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.pending)
    # 执行计划（内含，不独立暴露）
    execution_plan: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # 步骤日志
    step_logs: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    # 验证结果（内含）
    verification_results: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # 执行统计
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # relationships
    input_version: Mapped[AssetVersion] = relationship(foreign_keys=[input_version_id])
    output_version: Mapped[AssetVersion | None] = relationship(
        back_populates="produced_by_run", foreign_keys=[AssetVersion.produced_by_run_id]
    )


class Publication(Base):
    """发布记录：某个资产版本在什么条件下、以什么用途、带着哪些风险被正式交付。

    回答：这版资产何时、为何、以什么边界被交付给哪个下游。
    发布不是状态切换，而是正式交付动作。
    """

    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("asset_versions.id"), nullable=False
    )
    publication_type: Mapped[PublicationType] = mapped_column(
        Enum(PublicationType), default=PublicationType.draft
    )
    target: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. grpo-training, dpo-training
    output_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    output_format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 门禁通过记录
    gates_passed: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    # 保留风险
    retained_risks: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 替换关系（血缘）
    replaces_publication_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("publications.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # relationships
    asset_version: Mapped[AssetVersion] = relationship()
    replaces: Mapped[Publication | None] = relationship(remote_side=[id])
