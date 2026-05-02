"""FastAPI 应用入口，同时承载 API 和 Vue SPA 前端。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from dataclaw.config import settings
from dataclaw.database import engine
from dataclaw.domain.models import Base

# Vue 构建产物目录
DIST_DIR = Path(__file__).parent / "web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：确保数据目录存在，开发模式下自动建表
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Dataclaw",
    description="智能数据工作台 — 面向高质量 AI 数据资产闭环",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册 API 路由
from dataclaw.api.routes import router as api_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")


# 托管 Vue SPA 前端（构建后）
if DIST_DIR.exists():
    # 静态资源 (JS/CSS/images)
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    # SPA fallback: 所有非 /api 路径返回 index.html，由 Vue Router 处理
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 尝试直接返回文件（favicon.ico 等）
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # 否则返回 index.html 让 Vue Router 接管
        return FileResponse(DIST_DIR / "index.html")
