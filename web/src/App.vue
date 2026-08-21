<script setup>
import { onMounted, ref } from 'vue'
import { api } from './api'

const health = ref(null)
const err = ref('')

onMounted(async () => {
  try {
    health.value = await api.health()
  } catch (e) {
    err.value = e.message
  }
})
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand">📊 JobPulse 招聘情报站</div>
      <nav>
        <router-link to="/" exact-active-class="active">看板</router-link>
        <router-link to="/jobs" active-class="active">岗位列表</router-link>
        <router-link to="/predict" active-class="active">薪资预测</router-link>
      </nav>
      <div class="status" v-if="health">DB: {{ health.db }} · jobs {{ health.jobs.toLocaleString() }}</div>
      <div class="status err" v-else-if="err">⚠ {{ err }}</div>
    </header>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout { min-height: 100vh; }
.topbar {
  display: flex; align-items: center; gap: 28px;
  background: linear-gradient(135deg, #2b5876, #4e4376);
  color: #fff; padding: 14px 28px;
}
.brand { font-size: 18px; font-weight: 700; white-space: nowrap; }
nav { display: flex; gap: 6px; }
nav a { padding: 6px 14px; border-radius: 6px; font-size: 14px; opacity: .85; }
nav a:hover { background: rgba(255,255,255,.12); opacity: 1; }
nav a.active { background: rgba(255,255,255,.22); opacity: 1; font-weight: 600; }
.status { margin-left: auto; font-size: 12px; opacity: .85; }
.status.err { color: #ffd6d6; }
.content { padding: 20px 28px; }
</style>
