"""Ingest 服务：接入原始数据，创建 SourceMaterial + Asset + AssetVersion(v0)。"""

from sqlalchemy.ext.asyncio import AsyncSession

from dataclaw.domain.models import Asset, AssetVersion, SourceMaterial, VersionStatus
from dataclaw.domain.schemas import IngestRequest


async def ingest_source(db: AsyncSession, request: IngestRequest) -> Asset:
    """接入原始数据源，创建完整的资产链。"""
    # 1. 推断 source_type
    source_type = request.source_type
    if source_type == "auto":
        if request.source_uri.startswith("s3://"):
            source_type = "s3"
        elif request.source_uri.startswith("http"):
            source_type = "http"
        else:
            source_type = "local"

    # 2. 创建 SourceMaterial
    sm = SourceMaterial(
        name=request.name,
        source_uri=request.source_uri,
        source_type=source_type,
        metadata_=request.metadata,
    )
    db.add(sm)
    await db.flush()
    await db.refresh(sm)

    # 3. 推断 asset_type
    asset_type = "trajectory"  # 默认，后续可根据数据内容推断
    if request.metadata and "asset_type" in request.metadata:
        asset_type = request.metadata["asset_type"]

    # 4. 创建 Asset
    asset = Asset(
        name=request.name,
        asset_type=asset_type,
        source_material_id=sm.id,
        description=f"Ingested from {request.source_uri}",
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    # 5. 创建 AssetVersion v0 (raw)
    v0 = AssetVersion(
        asset_id=asset.id,
        version_number=0,
        status=VersionStatus.raw,
        storage_uri=request.source_uri,
    )
    db.add(v0)
    await db.commit()
    await db.refresh(asset)

    return asset
