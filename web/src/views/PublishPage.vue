<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api, type Publication } from '@/api/client'

const route = useRoute()
const assetName = computed(() => route.params.name as string)

const publications = ref<Publication[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    publications.value = await api.listPublications()
  } catch (e) {
    // pass
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-2">发布记录</h1>
    <p class="text-[#8b8d97] mb-6">发布不是导出动作，而是基于差异证据的正式交付判断。</p>

    <div class="card">
      <div v-if="loading" class="text-center py-8 text-[#8b8d97]">加载中...</div>

      <div v-else-if="publications.length === 0" class="text-center py-8 text-[#8b8d97]">
        <p>暂无发布记录</p>
        <p class="mt-2 text-xs">使用 <code class="text-indigo-400">dclaw publish &lt;asset&gt; &lt;version&gt; --target &lt;target&gt;</code></p>
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="text-left text-xs text-[#8b8d97] border-b border-[#2a2d37]">
            <th class="pb-2 font-medium">资产版本</th>
            <th class="pb-2 font-medium">类型</th>
            <th class="pb-2 font-medium">目标</th>
            <th class="pb-2 font-medium">门禁</th>
            <th class="pb-2 font-medium">发布时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pub in publications" :key="pub.id" class="border-b border-[#2a2d37]/50">
            <td class="py-3 font-mono text-xs">{{ pub.asset_version_id.slice(0, 8) }}</td>
            <td class="py-3">
              <span :class="['badge', pub.publication_type === 'formal' ? 'badge-success' : 'badge-warning']">
                {{ pub.publication_type }}
              </span>
            </td>
            <td class="py-3">{{ pub.target }}</td>
            <td class="py-3">
              <span v-if="pub.gates_passed" class="text-green-400 text-sm">
                {{ pub.gates_passed.filter(g => g.passed).length }}/{{ pub.gates_passed.length }} 通过
              </span>
              <span v-else class="text-[#8b8d97]">—</span>
            </td>
            <td class="py-3 text-sm text-[#8b8d97]">{{ new Date(pub.published_at).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 发布门禁详情 -->
    <div class="card mt-4">
      <h2 class="text-lg font-medium mb-3">发布门禁要求</h2>
      <ul class="space-y-2 text-sm text-[#8b8d97]">
        <li class="flex items-center gap-2"><span class="text-green-400">✓</span> 版本已完成体检或处理</li>
        <li class="flex items-center gap-2"><span class="text-green-400">✓</span> Reward 覆盖率达标</li>
        <li class="flex items-center gap-2"><span class="text-green-400">✓</span> Schema 验证通过</li>
        <li class="flex items-center gap-2"><span class="text-green-400">✓</span> 删除率未超阈值</li>
        <li class="flex items-center gap-2"><span class="text-yellow-400">⚠</span> 高风险需人工确认</li>
      </ul>
    </div>
  </div>
</template>
