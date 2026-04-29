"""API 路由：RESTful 接口供 CLI 和外部调用。"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataclaw.database import get_db
from dataclaw.domain.models import Asset, AssetVersion, ExecutionRun, Publication, SourceMaterial
from dataclaw.domain.schemas import (
    AssetOut,
    AssetVersionOut,
    DiffRequest,
    DiffResult,
    ExecutionRunOut,
    IngestRequest,
    InspectRequest,
    PublicationOut,
    PublishRequest,
    RunRequest,
    SourceMaterialOut,
)

router = APIRouter(tags=["dataclaw"])


# ─── Health ──────────────────────────────────────────────────────────────────


@router.get("/health")
async def health():
    return {"status": "ok", "service": "dataclaw"}


# ─── Ingest ──────────────────────────────────────────────────────────────────


@router.post("/ingest", response_model=AssetOut)
async def ingest(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    """接入原始数据，创建 SourceMaterial + Asset + AssetVersion(v0)。"""
    from dataclaw.services.ingest import ingest_source

    asset = await ingest_source(db, request)
    await db.refresh(asset)
    return asset


# ─── Assets ──────────────────────────────────────────────────────────────────


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).order_by(Asset.created_at.desc()))
    return result.scalars().all()


@router.get("/assets/{name}", response_model=AssetOut)
async def get_asset(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).where(Asset.name == name))
    asset = result.scalar_one()
    return asset


@router.get("/assets/{name}/versions", response_model=list[AssetVersionOut])
async def list_versions(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AssetVersion)
        .join(Asset)
        .where(Asset.name == name)
        .order_by(AssetVersion.version_number)
    )
    return result.scalars().all()


# ─── Inspect ─────────────────────────────────────────────────────────────────


@router.post("/inspect")
async def inspect(request: InspectRequest, db: AsyncSession = Depends(get_db)):
    """对资产版本执行数据体检。"""
    from dataclaw.services.inspect import inspect_version

    report = await inspect_version(db, request)
    return report


# ─── Run (Execute) ───────────────────────────────────────────────────────────


@router.post("/run", response_model=ExecutionRunOut)
async def run(request: RunRequest, db: AsyncSession = Depends(get_db)):
    """执行策略，产出新版本。"""
    from dataclaw.services.execute import execute_strategy

    run_record = await execute_strategy(db, request)
    return run_record


@router.get("/runs", response_model=list[ExecutionRunOut])
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExecutionRun).order_by(ExecutionRun.created_at.desc()).limit(50))
    return result.scalars().all()


# ─── Diff ────────────────────────────────────────────────────────────────────


@router.post("/diff", response_model=DiffResult)
async def diff(request: DiffRequest, db: AsyncSession = Depends(get_db)):
    """比较两个版本的差异。"""
    from dataclaw.services.diff import compare_versions

    return await compare_versions(db, request)


# ─── Publish ─────────────────────────────────────────────────────────────────


@router.post("/publish", response_model=PublicationOut)
async def publish(request: PublishRequest, db: AsyncSession = Depends(get_db)):
    """发布资产版本。"""
    from dataclaw.services.publish import publish_version

    return await publish_version(db, request)


@router.get("/publications", response_model=list[PublicationOut])
async def list_publications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Publication).order_by(Publication.published_at.desc()))
    return result.scalars().all()
