"""Inspect 服务：对资产版本执行数据体检。

两段式交互：
1. 第一段（秒级）：执行统计计算，生成硬数据
2. 第二段（10-30 秒）：LLM 解读异步追加（可选）
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataclaw.domain.models import Asset, AssetVersion, ProblemCluster, Severity, VersionStatus
from dataclaw.domain.schemas import InspectRequest


async def inspect_version(db: AsyncSession, request: InspectRequest) -> dict[str, Any]:
    """对资产版本执行体检，返回结构化报告。"""
    # 查找资产
    result = await db.execute(select(Asset).where(Asset.name == request.asset_name))
    asset = result.scalar_one_or_none()
    if not asset:
        return {"error": f"Asset '{request.asset_name}' not found"}

    # 查找版本
    if request.version is not None:
        ver_result = await db.execute(
            select(AssetVersion).where(
                AssetVersion.asset_id == asset.id,
                AssetVersion.version_number == request.version,
            )
        )
    else:
        ver_result = await db.execute(
            select(AssetVersion)
            .where(AssetVersion.asset_id == asset.id)
            .order_by(AssetVersion.version_number.desc())
            .limit(1)
        )
    version = ver_result.scalar_one_or_none()
    if not version:
        return {"error": "No version found"}

    # ─── 第一段：硬数据统计（不依赖 LLM）───────────────────────────────────
    # TODO: 实际实现需要读取数据源，这里生成占位报告
    report = {
        "asset": asset.name,
        "version": f"v{version.version_number}",
        "status": version.status.value,
        "record_count": version.record_count,
        "storage_uri": version.storage_uri,
        "quality_metrics": version.quality_metrics or {},
        "problems": [],
        "agent_analysis": None,  # 第二段异步填充
    }

    # 更新版本状态
    version.status = VersionStatus.inspected
    version.inspection_report = report
    await db.commit()

    return report
