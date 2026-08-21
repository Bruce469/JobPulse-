<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { api } from '../api'

const filters = ref({ city: '', category: '', education: '' })
const summary = ref(null)
const filtered = ref(null)
const chartsData = ref(null)
const loading = ref(false)
const error = ref('')

let charts = {}
const containerIds = ['c_salary', 'c_city', 'c_skills', 'c_cat', 'c_heat']

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.summary(filters.value)
    summary.value = data.summary
    filtered.value = data.filtered
    chartsData.value = data.charts
    renderCharts()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  const d = chartsData.value
  if (!d) return
  if (!charts.c_salary) {
    containerIds.forEach((id) => {
      charts[id] = echarts.init(document.getElementById(id))
    })
    window.addEventListener('resize', () => Object.values(charts).forEach((c) => c && c.resize()))
  }

  // ① 薪资分布
  const h = d.salary_hist
  charts.c_salary.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: h.bins.map((b, i) => `${Math.round(b / 1000)}-${Math.round((b + h.step) / 1000)}k`) },
    yAxis: { type: 'value', name: '岗位数' },
    series: [{ type: 'bar', data: h.counts, itemStyle: { color: '#4C72B0' } }],
  }, true)

  // ② 城市薪资对比（月薪中位数）
  charts.c_city.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: d.city_salary.cities },
    yAxis: { type: 'value', name: '月薪中位数（元）' },
    series: [{ type: 'bar', data: d.city_salary.medians, itemStyle: { color: '#55A868' } }],
  }, true)

  // ③ 技能需求 Top15（命中岗位占比）
  const top = [...d.skill_top].reverse()
  charts.c_skills.setOption({
    tooltip: { trigger: 'axis', formatter: (p) => `${p[0].name}：${(p[0].value * 100).toFixed(1)}%` },
    grid: { left: 100, right: 50, top: 10, bottom: 30 },
    xAxis: { type: 'value', name: '占比', axisLabel: { formatter: (v) => `${(v * 100).toFixed(0)}%` } },
    yAxis: { type: 'category', data: top.map((t) => t.name) },
    series: [{ type: 'bar', data: top.map((t) => t.ratio), itemStyle: { color: '#C44E52' } }],
  }, true)

  // ④ 岗位量占比
  charts.c_cat.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['40%', '68%'],
      data: d.category_dist,
      label: { formatter: '{b}\n{d}%' },
    }],
  }, true)

  // ⑤ 城市 × 类别 热力图
  const hm = d.heatmap
  charts.c_heat.setOption({
    tooltip: { position: 'top', formatter: (p) => `${hm.y[p.value[1]]}×${hm.x[p.value[0]]}：${p.value[2]} 条` },
    grid: { left: 80, top: 20, right: 40, bottom: 60 },
    xAxis: { type: 'category', data: hm.x, splitArea: { show: true } },
    yAxis: { type: 'category', data: hm.y, splitArea: { show: true } },
    visualMap: { min: 0, max: Math.max(...hm.data.map((x) => x[2]), 1), calculable: true, orient: 'horizontal', left: 'center', bottom: 0 },
    series: [{
      type: 'heatmap', data: hm.data,
      label: { show: true, fontSize: 9 },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.4)' } },
    }],
  }, true)
}

onMounted(load)
onBeforeUnmount(() => {
  Object.values(charts).forEach((c) => c && c.dispose())
  charts = {}
})
</script>

<template>
  <div>
    <div class="cards">
      <div class="card"><div class="num">{{ filtered?.total ?? '-' }}</div><div class="lbl">当前筛选岗位数</div></div>
      <div class="card"><div class="num">{{ filtered?.mean_salary ? filtered.mean_salary.toLocaleString() : '-' }}</div><div class="lbl">平均月薪（元）</div></div>
      <div class="card"><div class="num">{{ filtered?.median_salary ? filtered.median_salary.toLocaleString() : '-' }}</div><div class="lbl">月薪中位数（元）</div></div>
      <div class="card"><div class="num">{{ summary?.cities?.length ?? '-' }}</div><div class="lbl">覆盖城市</div></div>
    </div>

    <div class="filters">
      <label>城市
        <select v-model="filters.city" @change="load">
          <option value="">全部城市</option>
          <option v-for="c in summary?.cities || []" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
      <label>岗位类别
        <select v-model="filters.category" @change="load">
          <option value="">全部类别</option>
          <option v-for="c in summary?.categories || []" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
      <label>学历
        <select v-model="filters.education" @change="load">
          <option value="">全部学历</option>
          <option v-for="e in summary?.educations || []" :key="e" :value="e">{{ e }}</option>
        </select>
      </label>
      <span class="note" v-if="loading">加载中…</span>
      <span class="note err" v-if="error">⚠ {{ error }}（请先启动后端 python src/cli.py api）</span>
    </div>

    <div class="charts">
      <div class="panel"><h3>① 薪资分布（筛选后）</h3><div id="c_salary" class="chart"></div></div>
      <div class="panel"><h3>② 城市薪资对比（月薪中位数）</h3><div id="c_city" class="chart"></div></div>
      <div class="panel"><h3>③ 技能需求 Top15（命中岗位占比）</h3><div id="c_skills" class="chart"></div></div>
      <div class="panel"><h3>④ 岗位量占比（按类别）</h3><div id="c_cat" class="chart"></div></div>
      <div class="panel full"><h3>⑤ 城市 × 岗位类别 岗位量热力图</h3><div id="c_heat" class="chart" style="height: 360px"></div></div>
    </div>
    <div class="foot">数据来自 MySQL · 生成时间 {{ summary?.generated_at }}</div>
  </div>
</template>

<style scoped>
.cards { display: flex; gap: 14px; flex-wrap: wrap; }
.card { background: #fff; border-radius: 8px; padding: 14px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.08); min-width: 150px; }
.card .num { font-size: 26px; font-weight: 700; color: #2b5876; }
.card .lbl { font-size: 12px; color: #888; margin-top: 2px; }
.filters { display: flex; gap: 18px; flex-wrap: wrap; align-items: center; background: #fff; padding: 14px 20px; margin: 16px 0; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.filters label { font-size: 13px; color: #555; }
.filters select { padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 13px; }
.note { font-size: 12px; color: #999; }
.note.err { color: #c44e52; }
.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 10px; }
.panel h3 { margin: 6px 10px; font-size: 14px; color: #2b5876; }
.chart { width: 100%; height: 320px; }
.full { grid-column: 1 / -1; }
.foot { text-align: center; color: #999; font-size: 12px; padding: 14px 0 20px; }
</style>
