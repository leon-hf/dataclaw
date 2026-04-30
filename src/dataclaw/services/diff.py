"""Diff 服务：比较两个版本的差异。

比较不是执行后的附属报告，而是闭环中的正式判断步骤。
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataclaw.domain.models import Asset, AssetVersion, ProblemCluster
from dataclaw.domain.schemas import DiffRequest, DiffResult


async def compare_versions(db: AsyncSession, request: DiffRequest) -> DiffResult:
    """比较同一资产的两个版本。"""
    # 查找资产
    result = await db.execute(select(Asset).where(Asset.name == request.asset_name))
    asset = result.scalar_one_or_none()
    if not asset:
        raise ValueError(f"Asset '{request.asset_name}' not found")

    # 查找两个版本
    va_result = await db.execute(
        select(AssetVersion).where(
            AssetVersion.asset_id == asset.id,
            AssetVersion.version_number == request.version_a,
        )
    )
    vb_result = await db.execute(
        select(AssetVersion).where(
            AssetVersion.asset_id == asset.id,
            AssetVersion.version_number == request.version_b,
        )
    )
    version_a = va_result.scalar_one_or_none()
    version_b = vb_result.scalar_one_or_none()

    if not version_a or not version_b:
        raise ValueError("Version not found")

    # 计算指标差异
    metrics_a = version_a.quality_metrics or {}
    metrics_b = version_b.quality_metrics or {}
    all_keys = set(list(metrics_a.keys()) + list(metrics_b.keys()))
    metrics_diff: dict[str, Any] = {}
    for key in all_keys:
        a_val = metrics_a.get(key)
        b_val = metrics_b.get(key)
        delta = None
        if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
            delta = b_val - a_val
        metrics_diff[key] = {"a": a_val, "b": b_val, "delta": delta}

    # 查找问题分组变化
    clusters_a = await db.execute(
        select(ProblemCluster).where(ProblemCluster.asset_version_id == version_a.id)
    )
    clusters_b = await db.execute(
        select(ProblemCluster).where(ProblemCluster.asset_version_id == version_b.id)
    )
    ca_list = clusters_a.scalars().all()
    cb_list = clusters_b.scalars().all()

    ca_map = {c.cluster_key: c for c in ca_list}
    cb_map = {c.cluster_key: c for c in cb_list}

    cluster_changes = []
    for key in set(list(ca_map.keys()) + list(cb_map.keys())):
        change: dict[str, Any] = {"cluster_key": key}
        if key in ca_map and key in cb_map:
            change["status"] = "changed"
            change["count_a"] = ca_map[key].affected_count
            change["count_b"] = cb_map[key].affected_count
        elif key in ca_map:
            change["status"] = "resolved"
            change["count_a"] = ca_map[key].affected_count
            change["count_b"] = 0
        else:
            change["status"] = "new"
            change["count_a"] = 0
            change["count_b"] = cb_map[key].affected_count
        cluster_changes.append(change)

    return DiffResult(
        asset_name=request.asset_name,
        version_a=request.version_a,
        version_b=request.version_b,
        metrics_diff=metrics_diff,
        cluster_changes=cluster_changes,
        interpretation=None,  # 第二段 LLM 解读
    )
