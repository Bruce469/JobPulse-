<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'

const query = reactive({
  city: '', category: '', education: '', experience: '', job_type: '',
  keyword: '', source: '', page: 1, page_size: 10, sort_by: 'crawl_date', order: 'desc',
})
const meta = ref({ cities: [], categories: [], educations: [], sources: [] })
const result = ref({ total: 0, items: [] })
const loading = ref(false)
const error = ref('')

const EXPERIENCES = ['不限', '1年以内', '1-3年', '3-5年', '5-10年', '10年以上']
const JOB_TYPES = ['不限', '社招', '校招', '实习']

// 数据源下拉显示名（值仍为 source id）
const SOURCE_LABELS = {
  backup: 'GitHub 数据集',
  job51: '51job',
  iguopin: '国聘网',
  nowcoder: '牛客网',
}
const sourceLabel = (s) => SOURCE_LABELS[s] || s

async function load() {
  loading.value = true
  error.value = ''
  try {
    result.value = await api.jobs(query)
    if (!meta.value.cities.length) {
      meta.value = await api.meta()
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

function goPage(p) {
  if (p < 1 || p > result.value.total_pages) return
  query.page = p
  load()
}

watch(() => query.page_size, () => { query.page = 1; load() })
onMounted(load)

const fmtSalary = (r) => {
  if (r.salary_raw && r.salary_raw !== '面议') return r.salary_raw.replace(/[()]/g, '')
  return '面议'
}
</script>

<template>
  <div>
    <div class="toolbar">
      <select v-model="query.source"><option value="">全部数据源</option>
        <option v-for="s in meta.sources" :key="s" :value="s">{{ sourceLabel(s) }}</option></select>
      <select v-model="query.city"><option value="">全部城市</option>
        <option v-for="c in meta.cities" :key="c" :value="c">{{ c }}</option></select>
      <select v-model="query.category"><option value="">全部类别</option>
        <option v-for="c in meta.categories" :key="c" :value="c">{{ c }}</option></select>
      <select v-model="query.education"><option value="">全部学历</option>
        <option v-for="e in meta.educations" :key="e" :value="e">{{ e }}</option></select>
      <select v-model="query.experience"><option value="">全部经验</option>
        <option v-for="e in EXPERIENCES" :key="e" :value="e">{{ e }}</option></select>
      <select v-model="query.job_type"><option value="">全部类型</option>
        <option v-for="t in JOB_TYPES" :key="t" :value="t">{{ t }}</option></select>
      <input v-model="query.keyword" placeholder="搜索岗位 / 公司 / JD 关键词" @keyup.enter="search" />
      <button @click="search">搜索</button>
    </div>

    <div class="meta-line" v-if="!loading">
      共 {{ result.total.toLocaleString() }} 条
      <select v-model="query.sort_by" @change="load">
        <option value="crawl_date">按采集时间</option>
        <option value="post_date">按发布时间</option>
        <option value="salary_avg">按薪资</option>
      </select>
      <button class="mini" @click="query.order = query.order === 'desc' ? 'asc' : 'desc'; load()">
        {{ query.order === 'desc' ? '↓ 降序' : '↑ 升序' }}
      </button>
      <span class="err" v-if="error">⚠ {{ error }}</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>岗位</th><th>公司</th><th>城市</th><th>类别</th><th>薪资</th>
            <th>经验</th><th>学历</th><th>技能</th><th>发布时间</th><th>来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="j in result.items" :key="j.job_id">
            <td>
              <a :href="j.url" target="_blank" rel="noopener" class="title">{{ j.title }}</a>
              <div class="sub">{{ j.type }} · {{ j.industry }} {{ j.company_size || '' }}</div>
            </td>
            <td>{{ j.company }}</td>
            <td>{{ j.city }}</td>
            <td>{{ j.category }}</td>
            <td class="sal">{{ fmtSalary(j) }}</td>
            <td>{{ j.experience }}</td>
            <td>{{ j.education }}</td>
            <td>
              <span v-for="s in (j.skills || []).slice(0, 4)" :key="s" class="tag">{{ s }}</span>
              <span v-if="j.skills_count > 4" class="tag more">+{{ j.skills_count - 4 }}</span>
            </td>
            <td>{{ j.post_date || j.crawl_date || '-' }}</td>
            <td>{{ j.source }}</td>
          </tr>
          <tr v-if="!result.items.length && !loading"><td colspan="10" class="empty">无匹配岗位</td></tr>
        </tbody>
      </table>
    </div>

    <div class="pager" v-if="result.total_pages > 1">
      <button :disabled="query.page <= 1" @click="goPage(query.page - 1)">上一页</button>
      <span>第 {{ query.page }} / {{ result.total_pages }} 页</span>
      <button :disabled="query.page >= result.total_pages" @click="goPage(query.page + 1)">下一页</button>
      <select v-model.number="query.page_size" style="margin-left:12px">
        <option :value="10">10 条/页</option><option :value="20">20 条/页</option><option :value="50">50 条/页</option>
      </select>
    </div>
  </div>
</template>

<style scoped>
.toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; background: #fff; padding: 14px 20px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.toolbar select, .toolbar input { padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 13px; }
.toolbar input { width: 260px; }
.toolbar button { padding: 6px 16px; border: none; border-radius: 6px; background: #2b5876; color: #fff; cursor: pointer; }
.meta-line { display: flex; gap: 12px; align-items: center; margin: 14px 2px; font-size: 13px; color: #666; }
.meta-line select { padding: 4px 8px; border: 1px solid #ccc; border-radius: 6px; }
.mini { padding: 4px 10px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; }
.err { color: #c44e52; }
.table-wrap { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; white-space: nowrap; }
th { background: #f8f9fb; color: #555; font-weight: 600; }
tr:hover td { background: #fafbfd; }
.title { color: #2b5876; font-weight: 600; }
.sub { color: #999; font-size: 12px; margin-top: 2px; }
.sal { color: #c44e52; font-weight: 600; }
.tag { display: inline-block; margin: 1px 3px 1px 0; padding: 1px 8px; border-radius: 10px; background: #eef3f9; color: #2b5876; font-size: 12px; }
.tag.more { background: #f5f5f5; color: #999; }
.empty { text-align: center; color: #999; padding: 30px; }
.pager { display: flex; gap: 14px; align-items: center; justify-content: center; margin-top: 16px; font-size: 13px; color: #666; }
.pager button { padding: 5px 14px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; }
.pager button:disabled { opacity: .4; cursor: default; }
</style>
