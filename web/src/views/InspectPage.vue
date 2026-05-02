<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api, type AssetVersion, type InspectionReport } from '@/api/client'

const route = useRoute()
const assetName = computed(() => route.params.name as string)

const versions = ref<AssetVersion[]>([])
const selectedVersion = ref<number | null>(null)
const report = ref<InspectionReport | null>(null)
const loading = ref(false)
const inspecting = ref(false)

onMounted(async () => {
  if (!assetName.value) return
  loading.value = true
  try {
    versions.value = await api.listVersions(assetName.value)
    if (versions.value.length > 0) {
      selectedVersion.value = versions.value[versions.value.length - 1].version_number
      // 如果最新版本已有体检报告，直接展示
      const latest = versions.value[versions.value.length - 1]
      if (latest.inspection_report) {
        report.value = latest.inspection_report as any
      }
    }
  } catch (e) {
    // pass
  } finally {
    loading.value = false
  }
})

async function runInspection() {
  if (!assetName.value) return
  inspecting.value = true
  try {
    report.value = await api.inspect({
      asset_name: assetName.value,
      version: selectedVersion.value,
    })
  } catch (e) {
    // pass
  } finally {
    inspecting.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-2">数据体检</h1>
    <p class="text-[#8b8d97] mb-6" v-if="assetName">{{ assetName }}</p>
    <p class="text-[#8b8d97] mb-6" v-else>请从首页选择资产进行体检</p>

    <template v-if="assetName">
      <!-- 版本选择 + 执行体检 -->
      <div class="card mb-4">
        <div class="flex items-center gap-4">
          <div>
            <label class="text-xs text-[#8b8d97]">版本</label>
            <select v-model="selectedVersion" class="input ml-2">
              <option v-for="v in versions" :key="v.id" :value="v.version_number">
                v{{ v.version_number }} ({{ v.status }})
              </option>
            </select>
          </div>
          <button @click="runInspection" :disabled="inspecting" class="btn btn-primary">
            {{ inspecting ? '体检中...' : '执行体检' }}
          </button>
        </div>
      </div>

      <!-- 体检报告：第一段（硬数据） -->
      <div v-if="report" class="space-y-4">
        <div class="card">
          <h2 class="text-lg font-medium mb-3">基础指标</h2>
          <div class="grid grid-cols-3 gap-4">
            <div class="metric-card">
              <div class="metric-label">记录数</div>
              <div class="metric-value">{{ report.record_count ?? '—' }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">版本</div>
              <div class="metric-value">{{ report.version }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">状���</div>
              <div class="metric-value">{{ report.status }}</div>
            </div>
          </div>
        </div>

        <!-- 质量指标 -->
        <div v-if="report.quality_metrics && Object.keys(report.quality_metrics).length > 0" class="card">
          <h2 class="text-lg font-medium mb-3">质量信号</h2>
          <table class="w-full">
            <tbody>
              <tr v-for="(value, key) in report.quality_metrics" :key="key" class="border-b border-[#2a2d37]/50">
                <td class="py-2 text-[#8b8d97]">{{ key }}</td>
                <td class="py-2 font-mono">{{ value }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- ��题分组 -->
        <div v-if="report.problems && report.problems.length > 0" class="card">
          <h2 class="text-lg font-medium mb-3">问题分组</h2>
          <div v-for="p in report.problems" :key="p.cluster_key" class="mb-3 p-3 rounded bg-[#0f1117] border border-[#2a2d37]">
            <div class="flex items-center gap-2">
              <span :class="['badge', p.severity === 'high' ? 'badge-danger' : p.severity === 'medium' ? 'badge-warning' : 'badge-info']">
                {{ p.severity.toUpperCase() }}
              </span>
              <span class="font-medium">{{ p.label }}</span>
              <span class="text-xs text-[#8b8d97] ml-auto">{{ p.affected_count }} 条</span>
            </div>
            <p v-if="p.root_cause" class="text-sm text-[#8b8d97] mt-2">原因：{{ p.root_cause }}</p>
            <p v-if="p.recommendation" class="text-sm text-indigo-300 mt-1">建��：{{ p.recommendation }}</p>
          </div>
        </div>

        <!-- Agent 解读（第二段，异步） -->
        <div v-if="report.agent_analysis" class="card border-indigo-500/30">
          <h2 class="text-lg font-medium mb-3 text-indigo-400">Agent 解读</h2>
          <p class="whitespace-pre-wrap text-sm">{{ report.agent_analysis }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
