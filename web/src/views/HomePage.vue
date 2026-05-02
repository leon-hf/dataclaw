<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Asset, type ExecutionRun } from '@/api/client'

const assets = ref<Asset[]>([])
const recentRuns = ref<ExecutionRun[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [a, r] = await Promise.all([api.listAssets(), api.listRuns()])
    assets.value = a
    recentRuns.value = r
  } catch (e) {
    // API not available yet
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">数据资产概览</h1>

    <!-- P0 快速入口 -->
    <div class="grid grid-cols-3 gap-4 mb-8">
      <div class="card group cursor-pointer hover:border-indigo-500/50">
        <div class="text-indigo-400 text-sm font-medium mb-1">P0 链路一</div>
        <div class="font-medium">Rollout → RL 训练资产</div>
        <div class="text-xs text-[#8b8d97] mt-2">把运行轨迹变成可训练数据集</div>
      </div>
      <div class="card group cursor-pointer hover:border-indigo-500/50">
        <div class="text-indigo-400 text-sm font-medium mb-1">P0 链路二</div>
        <div class="font-medium">失败 → 反馈信号</div>
        <div class="text-xs text-[#8b8d97] mt-2">从失败轨迹提取偏好对和奖励信号</div>
      </div>
      <div class="card group cursor-pointer hover:border-indigo-500/50">
        <div class="text-indigo-400 text-sm font-medium mb-1">P0 链路三</div>
        <div class="font-medium">Policy 版本比较</div>
        <div class="text-xs text-[#8b8d97] mt-2">比较两版 policy 行为差异并重发布</div>
      </div>
    </div>

    <!-- 资产列表 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-medium">资产</h2>
        <span class="text-xs text-[#8b8d97]">{{ assets.length }} 个资���</span>
      </div>

      <div v-if="loading" class="text-center py-8 text-[#8b8d97]">加载中...</div>

      <div v-else-if="assets.length === 0" class="text-center py-8 text-[#8b8d97]">
        <p>暂无资产</p>
        <p class="mt-2 text-xs">使用 <code class="text-indigo-400">dclaw ingest &lt;uri&gt; --name &lt;name&gt;</code> 接入数据</p>
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="text-left text-xs text-[#8b8d97] border-b border-[#2a2d37]">
            <th class="pb-2 font-medium">名称</th>
            <th class="pb-2 font-medium">类型</th>
            <th class="pb-2 font-medium">状态</th>
            <th class="pb-2 font-medium">创建时间</th>
            <th class="pb-2 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="asset in assets" :key="asset.id" class="border-b border-[#2a2d37]/50">
            <td class="py-3 font-medium">{{ asset.name }}</td>
            <td class="py-3"><span class="badge badge-info">{{ asset.asset_type }}</span></td>
            <td class="py-3"><span class="badge badge-success">{{ asset.status }}</span></td>
            <td class="py-3 text-sm text-[#8b8d97]">{{ new Date(asset.created_at).toLocaleString() }}</td>
            <td class="py-3 space-x-2">
              <RouterLink :to="`/inspect/${asset.name}`" class="btn btn-sm">体检</RouterLink>
              <RouterLink :to="`/diff/${asset.name}`" class="btn btn-sm">比较</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 最近执行 -->
    <div v-if="recentRuns.length > 0" class="card mt-4">
      <h2 class="text-lg font-medium mb-4">最近执行</h2>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs text-[#8b8d97] border-b border-[#2a2d37]">
            <th class="pb-2 font-medium">策略</th>
            <th class="pb-2 font-medium">状态</th>
            <th class="pb-2 font-medium">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in recentRuns" :key="run.id" class="border-b border-[#2a2d37]/50">
            <td class="py-3">{{ run.strategy_id }}</td>
            <td class="py-3">
              <span :class="['badge', run.status === 'completed' ? 'badge-success' : 'badge-warning']">
                {{ run.status }}
              </span>
            </td>
            <td class="py-3 text-sm text-[#8b8d97]">{{ new Date(run.created_at).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
