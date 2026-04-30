"""Publish 服务：发布资产版本。

发布不是状态切换，而是正式交付动作。
必须记录：发布对象、目标用途、门禁通过、保留风险、影响下游。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataclaw.domain.models import (
    Asset,
    AssetVersion,
    Publication,
    PublicationType,
    VersionStatus,
)
from dataclaw.domain.schemas import PublishRequest


async def publish_version(db: AsyncSession, request: PublishRequest) -> Publication:
    """发布资产版本。"""
    # 查找资产和版本
    result = await db.execute(select(Asset).where(Asset.name == request.asset_name))
    asset = result.scalar_one_or_none()
    if not asset:
        raise ValueError(f"Asset '{request.asset_name}' not found")

    ver_result = await db.execute(
        select(AssetVersion).where(
            AssetVersion.asset_id == asset.id,
            AssetVersion.version_number == request.version,
        )
    )
    version = ver_result.scalar_one_or_none()
    if not version:
        raise ValueError(f"Version v{request.version} not found")

    # 执行发布门禁检查
    gates_passed = []
    retained_risks = []

    # 基本门禁：版本必须已被处理或体检过
    if version.status in (VersionStatus.processed, VersionStatus.inspected):
        gates_passed.append({"gate": "version_status", "passed": True, "detail": f"Status is {version.status.value}"})
    else:
        gates_passed.append({"gate": "version_status", "passed": False, "detail": f"Status is {version.status.value}, expected processed/inspected"})

    # TODO: 更多门禁检查（质量指标、覆盖率、PII、删除率等）

    # 创建 Publication
    pub_type = PublicationType.draft if request.publication_type == "draft" else PublicationType.formal
    pub = Publication(
        asset_version_id=version.id,
        publication_type=pub_type,
        target=request.target,
        output_format=request.output_format,
        gates_passed=gates_passed,
        retained_risks=retained_risks,
        note=request.note,
    )

    # 处理替换关系
    if request.replaces:
        # TODO: 解析 "asset_name:vN" 格式，查找被替换的 Publication
        pass

    db.add(pub)

    # 更新版本状态
    version.status = VersionStatus.published

    await db.commit()
    await db.refresh(pub)
    return pub
