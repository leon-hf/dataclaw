<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-[#0f1117] text-[#e4e4e7]">
    <!-- Sidebar -->
    <aside class="fixed left-0 top-0 h-full w-56 bg-[#1a1d27] border-r border-[#2a2d37] flex flex-col">
      <div class="p-5">
        <h1 class="text-lg font-bold text-indigo-400">Dataclaw</h1>
        <p class="text-xs text-[#8b8d97] mt-1">智能数据工作台</p>
      </div>
      <nav class="flex-1 px-3 space-y-1">
        <RouterLink
          to="/"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="i-nav">⊞</span> 首页
        </RouterLink>
        <RouterLink
          to="/inspect/"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="i-nav">◉</span> 数据体检
        </RouterLink>
        <RouterLink
          to="/diff/"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="i-nav">⇄</span> 差异比较
        </RouterLink>
        <RouterLink
          to="/run/"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="i-nav">▶</span> 执行记录
        </RouterLink>
        <RouterLink
          to="/publish/"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="i-nav">↗</span> 发布
        </RouterLink>
      </nav>
      <div class="p-4 border-t border-[#2a2d37] text-xs text-[#8b8d97]">
        v0.1.0
      </div>
    </aside>

    <!-- Main content -->
    <main class="ml-56 p-8">
      <slot />
    </main>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.nav-item {
  @apply flex items-center gap-2 px-3 py-2 rounded-md text-sm text-[#8b8d97] hover:text-[#e4e4e7] hover:bg-[#2a2d37] transition-colors;
}
.nav-item-active {
  @apply text-[#e4e4e7] bg-[#2a2d37];
}
.i-nav {
  @apply w-4 text-center;
}
</style>
