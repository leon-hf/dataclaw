"""策略注册表：管理 Execution Strategy 的注册和获取。

Execution Strategy 是对某类目标的结构化决策模板，不是固定步骤列表。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyStep:
    """执行步骤定义。"""
    name: str
    description: str
    capability: str  # 语义能力 ID (e.g. "reward.rescore")
    parameters: dict[str, Any] = field(default_factory=dict)
    verification_point: str | None = None


@dataclass
class ExecutionStrategy:
    """执行策略定义。"""
    id: str
    name: str
    description: str
    applicable_asset_types: list[str]
    required_observations: list[str]
    steps_template: list[StrategyStep]
    verification_points: list[str]
    risk_level: str = "medium"  # low, medium, high

    def compile_plan(
        self,
        input_version: Any,
        clusters: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """根据当前上下文编译执行计划。"""
        return {
            "strategy_id": self.id,
            "input_version_id": input_version.id,
            "input_version_number": input_version.version_number,
            "clusters": clusters,
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "capability": step.capability,
                    "parameters": {**step.parameters, **(parameters or {})},
                }
                for step in self.steps_template
            ],
            "verification_points": self.verification_points,
            "risk_level": self.risk_level,
        }


# ─── P0 策略模板 ─────────────────────────────────────────────────────────────

STRATEGY_REGISTRY: dict[str, ExecutionStrategy] = {}


def register_strategy(strategy: ExecutionStrategy) -> None:
    STRATEGY_REGISTRY[strategy.id] = strategy


def get_strategy(strategy_id: str) -> ExecutionStrategy:
    if strategy_id not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Strategy '{strategy_id}' not found. Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return STRATEGY_REGISTRY[strategy_id]


def list_strategies() -> list[ExecutionStrategy]:
    return list(STRATEGY_REGISTRY.values())


# ─── 注册 P0 策略 ────────────────────────────────────────────────────────────

register_strategy(ExecutionStrategy(
    id="rollout_to_rl_asset",
    name="Rollout → RL 训练资产",
    description="把运行轨迹从日志变成可训练、可验证、可发布的 RL 数据资产",
    applicable_asset_types=["trajectory"],
    required_observations=["structure_check", "reward_coverage", "length_distribution"],
    steps_template=[
        StrategyStep(
            name="rescore_reward",
            description="对缺失 reward 的轨迹重新计算奖励信号",
            capability="reward.rescore",
            verification_point="reward_coverage > 95%",
        ),
        StrategyStep(
            name="filter_anomalies",
            description="过滤异常长度轨迹（过短或过长）",
            capability="curate.filter",
            parameters={"min_steps": 2, "max_steps": 50},
            verification_point="deletion_rate < 10%",
        ),
        StrategyStep(
            name="normalize_format",
            description="规范化为训练格式",
            capability="normalize.to_training_format",
            parameters={"target_format": "grpo"},
            verification_point="schema_validation_passed",
        ),
    ],
    verification_points=[
        "reward_coverage > 95%",
        "deletion_rate < 10%",
        "schema_validation_passed",
    ],
    risk_level="medium",
))

register_strategy(ExecutionStrategy(
    id="failure_to_signal_assets",
    name="失败轨迹 → 反馈信号资产",
    description="从失败轨迹中提取偏好对和过程奖励信号",
    applicable_asset_types=["trajectory"],
    required_observations=["failure_analysis", "cluster_identification"],
    steps_template=[
        StrategyStep(
            name="generate_preference_pairs",
            description="为 almost-correct 轨迹生成 (rejected, chosen) 偏好对",
            capability="derive.preference_pairs",
            verification_point="chosen_passes_tests",
        ),
        StrategyStep(
            name="annotate_process_rewards",
            description="在决策点标注步骤级奖励信号",
            capability="reward.step_level_annotate",
            verification_point="wrong_turn_before_failure",
        ),
        StrategyStep(
            name="filter_low_value",
            description="丢弃低价值失败（工具错误、退化轨迹）",
            capability="curate.filter",
            parameters={"filter_clusters": ["tool_error", "degenerate"]},
        ),
    ],
    verification_points=[
        "chosen_passes_tests",
        "wrong_turn_before_failure",
        "task_distribution_balanced",
    ],
    risk_level="medium",
))

register_strategy(ExecutionStrategy(
    id="policy_compare_and_republish",
    name="策略版本比较与重发布",
    description="比较两版 policy 的行为差异，更新 replay 资产并重发布",
    applicable_asset_types=["trajectory"],
    required_observations=["cross_version_comparison", "behavior_diff"],
    steps_template=[
        StrategyStep(
            name="quick_inspect",
            description="对新版本快速体检",
            capability="inspect.quick",
        ),
        StrategyStep(
            name="behavior_comparison",
            description="在重叠任务上比较行为差异",
            capability="compare.behavior",
            verification_point="improvement_confirmed",
        ),
        StrategyStep(
            name="clean_and_republish",
            description="清洗新版本并替换发布",
            capability="normalize.to_training_format",
        ),
    ],
    verification_points=[
        "improvement_confirmed",
        "no_critical_regression",
    ],
    risk_level="low",
))
