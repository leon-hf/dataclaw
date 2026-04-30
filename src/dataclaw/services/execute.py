"""Execute 服务：执行策略，产出新资产版本。

流程：Strategy -> Compile Plan -> Execute Steps -> Materialize Version
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataclaw.domain.models import (
    Asset,
    AssetVersion,
    ExecutionRun,
    RunStatus,
    VersionStatus,
)
from dataclaw.domain.schemas import RunRequest


async def execute_strategy(db: AsyncSession, request: RunRequest) -> ExecutionRun:
    """执行策略并产出新版本。"""
    # 查找资产和最新版本
    result = await db.execute(select(Asset).where(Asset.name == request.asset_name))
    asset = result.scalar_one_or_none()
    if not asset:
        raise ValueError(f"Asset '{request.asset_name}' not found")

    ver_result = await db.execute(
        select(AssetVersion)
        .where(AssetVersion.asset_id == asset.id)
        .order_by(AssetVersion.version_number.desc())
        .limit(1)
    )
    input_version = ver_result.scalar_one_or_none()
    if not input_version:
        raise ValueError("No version found for this asset")

    # 加载策略定义
    from dataclaw.strategies.registry import get_strategy

    strategy = get_strategy(request.strategy_id)

    # 编译执行计划
    plan = strategy.compile_plan(
        input_version=input_version,
        clusters=request.clusters,
        parameters=request.parameters,
    )

    # 创建 ExecutionRun 记录
    run = ExecutionRun(
        asset_id=asset.id,
        input_version_id=input_version.id,
        strategy_id=request.strategy_id,
        status=RunStatus.running,
        execution_plan=plan,
        step_logs=[],
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    # 执行步骤（简化版：第一版直接标记完成）
    # TODO: 实际实现需要按 plan 中的 steps 逐步执行
    try:
        # 物化新版本
        new_version_number = input_version.version_number + 1
        new_version = AssetVersion(
            asset_id=asset.id,
            version_number=new_version_number,
            status=VersionStatus.processed,
            produced_by_run_id=run.id,
        )
        db.add(new_version)

        run.status = RunStatus.completed
        run.completed_at = datetime.now(timezone.utc)
        run.step_logs = [{"step": "placeholder", "status": "completed", "message": "Strategy execution placeholder"}]

    except Exception as e:
        run.status = RunStatus.failed
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(run)
    return run
