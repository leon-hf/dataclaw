<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api, type AssetVersion, type DiffResult } from '@/api/client'

const route = useRoute()
const assetName = computed(() => route.params.name as string)

const versions = ref<AssetVersion[]>([])
const versionA = ref<number>(0)
const versionB = ref<number>(1)
const diffResult = ref<DiffResult | null>(null)
const loading = ref(false)

onMounted(async () => {
  if (!assetName.value) return
  try {
    versions.value = await api.listVersions(assetName.value)
    if (versions.value.length >= 2) {
      versionA.value = versions.value[versions.value.length - 2].version_number
      versionB.value = versions.value[versions.value.length - 1].version_number
    }
  } catch (e) {
    // pass
  }
})

async function runDiff() {
  if (!assetName.value) return
  loading.value = true
  try {
    diffResult.value = await api.diff({
      asset_name: assetName.value,
      version_a: versionA.value,
      version_b: versionB.value,
    })
  } catch (e) {
    // pass
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-2">差异比较</h1>
    <p class="text-[#8b8d97] mb-6" v-if="assetName">{{ assetName }}</p>
    <p class="text-[#8b8d97] mb-6" v-else>���从首页选择资产进行比较</p>

    <template v-if="assetName">
      <!-- 版本选择 -->
      <div class="card mb-4">
        <div class="flex items-center gap-4">
          <div>
            <label class="text-xs text-[#8b8d97]">版本 A</label>
            <select v-model="versionA" class="input ml-2">
              <option v-for="v in versions" :key="v.id" :value="v.version_number">
                v{{ v.version_number }}
              </option>
            </select>
          </div>
          <span class="text-[#8b8d97]">→</span>
          <div>
            <label class="text-xs text-[#8b8d97]">版本 B</label>
            <select v-model="versionB" class="input ml-2">
              <option v-for="v in versions" :key="v.id" :value="v.version_number">
                v{{ v.version_number }}
              </option>
            </select>
          </div>
          <button @click="runDiff" :disabled="loading" class="btn btn-primary">
            {{ loading ? '比较中...' : '执行比���' }}
          </button>
        </div>
      </div>

      <!-- Diff 结果 -->
      <div v-if="diffResult" class="space-y-4">
        <!-- 指标对比表 -->
        <div class="card">
          <h2 class="text-lg font-medium mb-3">指标变化</h2>
          <table class="w-full" v-if="Object.keys(diffResult.metrics_diff).length > 0">
            <thead>
              <tr class="text-left text-xs text-[#8b8d97] border-b border-[#2a2d37]">
                <th class="pb-2">指标</th>
                <th class="pb-2">v{{ diffResult.version_a }}</th>
                <th class="pb-2">v{{ diffResult.version_b }}</th>
                <th class="pb-2">变化</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(val, key) in diffResult.metrics_diff" :key="key" class="border-b border-[#2a2d37]/50">
                <td class="py-2 text-[#8b8d97]">{{ key }}</td>
                <td class="py-2 font-mono">{{ val.a ?? '—' }}</td>
                <td class="py-2 font-mono">{{ val.b ?? '—' }}</td>
                <td class="py-2 font-mono" :class="val.delta > 0 ? 'text-green-400' : val.delta < 0 ? 'text-red-400' : ''">
                  {{ val.delta != null ? (val.delta > 0 ? '+' : '') + val.delta : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="text-[#8b8d97]">暂无指标数据</p>
        </div>

        <!-- 问题分组变化 -->
        <div v-if="diffResult.cluster_changes.length > 0" class="card">
          <h2 class="text-lg font-medium mb-3">��题分组变化</h2>
          <div v-for="c in diffResult.cluster_changes" :key="c.cluster_key" class="flex items-center gap-3 py-2 border-b border-[#2a2d37]/50">
            <span :class="['badge', c.status === 'resolved' ? 'badge-success' : c.status === 'new' ? 'badge-danger' : 'badge-warning']">
              {{ c.status === 'resolved' ? '已解���' : c.status === 'new' ? '新增' : '变化' }}
            </span>
            <span>{{ c.cluster_key }}</span>
            <span class="ml-auto text-sm text-[#8b8d97]">
              {{ c.count_a }} → {{ c.count_b }}
            </span>
          </div>
        </div>

        <!-- Agent 解读 -->
        <div v-if="diffResult.interpretation" class="card border-indigo-500/30">
          <h2 class="text-lg font-medium mb-3 text-indigo-400">Agent 解读</h2>
          <p class="whitespace-pre-wrap text-sm">{{ diffResult.interpretation }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
