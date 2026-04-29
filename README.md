# Dataclaw

**智能数据工作台** — 面向高质量 AI 数据资产闭环。

> 对外：面向高质量 AI 数据资产闭环的智能数据工作台  
> 对内：以数据质量为核心目标、由 Agent 引导决策、由系统负责规模化执行与验证的数据控制平面

## 快速开始

```bash
# 安装
pip install -e .

# 启动服务（Web Console + API）
dclaw serve --reload

# 或直接使用 CLI
dclaw ingest s3://my-bucket/rollouts/ --name "coding-v3-rollouts"
dclaw inspect coding-v3-rollouts
dclaw run --strategy rollout_to_rl_asset --asset coding-v3-rollouts --confirm
dclaw diff coding-v3-rollouts 0 1
dclaw publish coding-v3-rollouts 1 --target grpo-training
```

## 架构

```
src/dataclaw/
├── cli/          ← CLI 入口 (dclaw 命令)
├── api/          ← RESTful API (FastAPI)
├── web/          ← Web Console (Jinja2 + HTMX, 前后端不分离)
├── domain/       ← 领域模型 (6 个核心对象)
├── services/     ← 业务逻辑 (ingest, inspect, execute, diff, publish)
├── strategies/   ← 执行策略层 (Strategy 注册与编译)
├── execution/    ← 执行编译与运行时
├── governance/   ← 治理与验证层 (门禁、审计)
├── adapters/     ← 外部适配器 (S3, LLM, Reward Service)
├── config.py     ← 应用配置
└── database.py   ← 数据库连接
```

## 核心对象

| 对象 | 说明 |
|------|------|
| `SourceMaterial` | 原始数据（从哪里来） |
| `Asset` | 资产（长期身份，值得持续维护） |
| `AssetVersion` | 资产版本（可比较、可验证的状态快照） |
| `ProblemCluster` | 问题分组（识别出的质量问题或失败模式） |
| `ExecutionRun` | 处理记录（一次改进动作的完整记录） |
| `Publication` | 发布记录（正式交付，带门禁和证据） |

## P0 策略

| 策略 ID | 用途 |
|---------|------|
| `rollout_to_rl_asset` | 运行轨迹 → 可训练 RL 数据集 |
| `failure_to_signal_assets` | 失败轨迹 → 偏好对 / 过程奖励信号 |
| `policy_compare_and_republish` | 策略版本比较与重发布 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 数据库迁移
alembic upgrade head

# 运行测试
pytest

# 类型检查
mypy src/dataclaw/

# 代码检查
ruff check src/
```
