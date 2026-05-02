<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type ExecutionRun } from '@/api/client'

const runs = ref<ExecutionRun[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    runs.value = await api.listRuns()
  } catch (e) {
    // pass
  } finally {
    loading.value = false
  }
})

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'badge-success'
    case 'running': return 'badge-info'
    case 'failed': return 'badge-danger'
    default: return 'badge-warning'
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">执行记录</h1>

    <div class="card">
      <div v-if="loading" class="text-center py-8 text-[#8b8d97]">加载中...</div>

      <div v-else-if="runs.length === 0" class="text-center py-8 text-[#8b8d97]">
        暂无执行记录
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="text-left text-xs text-[#8b8d97] border-b border-[#2a2d37]">
            <th class="pb-2 font-medium">ID</th>
            <th class="pb-2 font-medium">策略</th>
            <th class="pb-2 font-medium">状态</th>
            <th class="pb-2 font-medium">开始时间</th>
            <th class="pb-2 font-medium">耗时</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.id" class="border-b border-[#2a2d37]/50 hover:bg-[#2a2d37]/30 cursor-pointer">
            <td class="py-3 font-mono text-xs">{{ run.id.slice(0, 8) }}</td>
            <td class="py-3">{{ run.strategy_id }}</td>
            <td class="py-3">
              <span :class="['badge', statusColor(run.status)]">{{ run.status }}</span>
            </td>
            <td class="py-3 text-sm text-[#8b8d97]">
              {{ run.started_at ? new Date(run.started_at).toLocaleString() : '—' }}
            </td>
            <td class="py-3 text-sm text-[#8b8d97]">
              <template v-if="run.started_at && run.completed_at">
                {{ Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000) }}s
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 执行详情（展开时展示步骤日志） -->
  </div>
</template>
