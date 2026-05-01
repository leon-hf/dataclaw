"""Dataclaw CLI — dclaw 命令行入口。

主命令对应设计文档中的用户故事：
  dclaw ingest   — 接入原始数据
  dclaw inspect  — 数据体检
  dclaw run      — 执行策略
  dclaw diff     — 版本差异比较
  dclaw publish  — 发布资产版本
  dclaw serve    — 启动 Web Console + API
"""

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="dclaw",
    help="Dataclaw — 智能数据工作台，面向高质量 AI 数据资产闭环",
    no_args_is_help=True,
)
console = Console()


async def _ensure_db():
    """确保数据库表存在。"""
    from dataclaw.database import engine
    from dataclaw.domain.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.command()
def ingest(
    source_uri: str = typer.Argument(..., help="数据源 URI (s3://, file://, http://)"),
    name: str = typer.Option(..., "--name", "-n", help="资产名称"),
    source_type: str = typer.Option("auto", "--type", "-t", help="源类型: s3, local, http"),
):
    """接入原始数据，创建资产和初始版本 (v0)。"""
    import asyncio
    from dataclaw.services.ingest import ingest_source
    from dataclaw.database import async_session_factory
    from dataclaw.domain.schemas import IngestRequest

    async def _run():
        await _ensure_db()
        async with async_session_factory() as db:
            request = IngestRequest(source_uri=source_uri, name=name, source_type=source_type)
            asset = await ingest_source(db, request)
            await db.refresh(asset)
            return asset

    asset = asyncio.run(_run())
    console.print(f"[green]✓[/green] Ingested from {source_uri}")
    console.print(f"  Asset created: [bold]{asset.name}[/bold]")
    console.print(f"  Version: v0 (raw)")
    console.print(f"  Starting inspection...")


@app.command()
def inspect(
    asset_name: str = typer.Argument(..., help="资产名称"),
    version: int = typer.Option(None, "--version", "-v", help="版本号（默认最新）"),
    focus: str = typer.Option(None, "--focus", "-f", help="聚焦: failures, rewards"),
):
    """对资产版本执行数据体检。"""
    import asyncio
    from dataclaw.services.inspect import inspect_version
    from dataclaw.database import async_session_factory
    from dataclaw.domain.schemas import InspectRequest

    async def _run():
        await _ensure_db()
        async with async_session_factory() as db:
            request = InspectRequest(asset_name=asset_name, version=version, focus=focus)
            return await inspect_version(db, request)

    report = asyncio.run(_run())
    console.print(f"\n[bold]=== Inspection Report: {asset_name} ===[/bold]\n")
    if report:
        for key, value in report.items():
            console.print(f"  {key}: {value}")
    else:
        console.print("  [yellow]No report generated (asset or version not found)[/yellow]")


@app.command()
def run(
    strategy: str = typer.Option(..., "--strategy", "-s", help="执行策略 ID"),
    asset_name: str = typer.Option(None, "--asset", "-a", help="资产名称"),
    clusters: str = typer.Option(None, "--clusters", "-c", help="问题分组（逗号分隔）"),
    confirm: bool = typer.Option(False, "--confirm", help="确认执行"),
):
    """执行策略，产出新版本。"""
    import asyncio
    from dataclaw.services.execute import execute_strategy
    from dataclaw.database import async_session_factory
    from dataclaw.domain.schemas import RunRequest

    cluster_list = clusters.split(",") if clusters else None

    async def _run():
        await _ensure_db()
        async with async_session_factory() as db:
            request = RunRequest(
                asset_name=asset_name or "",
                strategy_id=strategy,
                clusters=cluster_list,
                confirm=confirm,
            )
            return await execute_strategy(db, request)

    result = asyncio.run(_run())
    console.print(f"[green]✓[/green] Execution Run created: {result.id}")
    console.print(f"  Strategy: {result.strategy_id}")
    console.print(f"  Status: {result.status}")


@app.command()
def diff(
    asset_name: str = typer.Argument(..., help="资产名称"),
    version_a: int = typer.Argument(..., help="版本 A"),
    version_b: int = typer.Argument(..., help="版本 B"),
):
    """比较两个版本的差异。"""
    import asyncio
    from dataclaw.services.diff import compare_versions
    from dataclaw.database import async_session_factory
    from dataclaw.domain.schemas import DiffRequest

    async def _run():
        await _ensure_db()
        async with async_session_factory() as db:
            request = DiffRequest(asset_name=asset_name, version_a=version_a, version_b=version_b)
            return await compare_versions(db, request)

    result = asyncio.run(_run())
    console.print(f"\n[bold]=== Diff: {asset_name} v{version_a} → v{version_b} ===[/bold]\n")
    if result.metrics_diff:
        table = Table(title="Metrics")
        table.add_column("Metric")
        table.add_column(f"v{version_a}")
        table.add_column(f"v{version_b}")
        table.add_column("Change")
        for key, vals in result.metrics_diff.items():
            table.add_row(key, str(vals.get("a", "-")), str(vals.get("b", "-")), str(vals.get("delta", "")))
        console.print(table)


@app.command()
def publish(
    asset_name: str = typer.Argument(..., help="资产名称"),
    version: int = typer.Argument(..., help="版本号"),
    target: str = typer.Option(..., "--target", "-t", help="目标用途 (e.g. grpo-training)"),
    note: str = typer.Option(None, "--note", help="发布说明"),
    replaces: str = typer.Option(None, "--replaces", help="替换的发布 (asset:vN)"),
):
    """发布资产版本。"""
    import asyncio
    from dataclaw.services.publish import publish_version
    from dataclaw.database import async_session_factory
    from dataclaw.domain.schemas import PublishRequest

    async def _run():
        await _ensure_db()
        async with async_session_factory() as db:
            request = PublishRequest(
                asset_name=asset_name,
                version=version,
                target=target,
                note=note,
                replaces=replaces,
            )
            return await publish_version(db, request)

    pub = asyncio.run(_run())
    console.print(f"\n[bold]=== Publication Record ===[/bold]")
    console.print(f"  Asset: {asset_name}")
    console.print(f"  Version: v{version}")
    console.print(f"  Target: {target}")
    console.print(f"  Type: {pub.publication_type}")
    console.print(f"  Published at: {pub.published_at}")
    if pub.gates_passed:
        for gate in pub.gates_passed:
            console.print(f"  [green]✓[/green] {gate}")
    console.print(f"\n[green]✓ Ready.[/green]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="监听地址"),
    port: int = typer.Option(8000, "--port", "-p", help="监听端口"),
    reload: bool = typer.Option(False, "--reload", help="开发模式热重载"),
):
    """启动 Dataclaw Web Console + API 服务。"""
    import uvicorn

    console.print(f"[bold]Dataclaw[/bold] starting at http://{host}:{port}")
    console.print(f"  API docs: http://{host}:{port}/docs")
    console.print(f"  Web console: http://{host}:{port}/")
    uvicorn.run("dataclaw.app:app", host=host, port=port, reload=reload)


@app.command()
def assets():
    """列出所有资产。"""
    import asyncio
    from sqlalchemy import select
    from dataclaw.database import async_session_factory
    from dataclaw.domain.models import Asset

    async def _run():
        await _ensure_db()
        async with async_session_factory() as db:
            result = await db.execute(select(Asset).order_by(Asset.created_at.desc()))
            return result.scalars().all()

    items = asyncio.run(_run())
    if not items:
        console.print("[yellow]No assets found. Use 'dclaw ingest' to add data.[/yellow]")
        return

    table = Table(title="Assets")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Created")
    for a in items:
        table.add_row(a.name, a.asset_type, a.status.value, str(a.created_at)[:16])
    console.print(table)


if __name__ == "__main__":
    app()
