<script setup>
import { reactive, ref } from 'vue'
import { api } from '../api'

const form = reactive({
  job_title: '数据分析师',
  city: '北京',
  job_category: '数据分析',
  education_req: '本科',
  experience_req: '1-3年',
  job_type: '社招',
  industry: '互联网',
  company_size: '1000-5000人',
  skills: 'SQL, Python, Excel',
})
const result = ref(null)
const error = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  error.value = ''
  result.value = null
  const payload = {
    ...form,
    skills: form.skills.split(/[,，、\s]+/).filter(Boolean),
  }
  try {
    result.value = await api.predict(payload)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="wrap">
    <div class="form">
      <h3>🎯 薪资在线预测（XGBoost）</h3>
      <label>岗位标题 <input v-model="form.job_title" /></label>
      <label>城市 <input v-model="form.city" placeholder="如 北京" /></label>
      <label>岗位类别
        <select v-model="form.job_category">
          <option>数据分析</option><option>数据科学</option><option>大数据</option><option>算法</option><option>BI数仓</option>
        </select>
      </label>
      <label>学历要求
        <select v-model="form.education_req">
          <option>不限</option><option>大专</option><option>本科</option><option>硕士</option><option>博士</option>
        </select>
      </label>
      <label>经验要求
        <select v-model="form.experience_req">
          <option>不限</option><option>1年以内</option><option>1-3年</option><option>3-5年</option><option>5-10年</option><option>10年以上</option>
        </select>
      </label>
      <label>岗位类型
        <select v-model="form.job_type"><option>社招</option><option>校招</option><option>实习</option></select>
      </label>
      <label>行业 <input v-model="form.industry" /></label>
      <label>公司规模
        <select v-model="form.company_size">
          <option value="">未知</option><option>50人以下</option><option>50-150人</option><option>150-500人</option>
          <option>500-1000人</option><option>1000-5000人</option><option>5000-10000人</option><option>10000人以上</option>
        </select>
      </label>
      <label>技能关键词 <input v-model="form.skills" placeholder="逗号分隔，如 SQL, Python" /></label>
      <button :disabled="loading" @click="submit">{{ loading ? '预测中…' : '开始预测' }}</button>
      <div class="err" v-if="error">⚠ {{ error }}（提示：请先运行 python src/cli.py model 导出模型）</div>
    </div>

    <div class="result" v-if="result">
      <h3>预测结果</h3>
      <div class="big">{{ result.predicted_salary_avg.toLocaleString() }} 元/月</div>
      <div class="band">参考区间：{{ result.salary_band }}</div>
      <div class="note">{{ result.note }}</div>
    </div>
  </div>
</template>

<style scoped>
.wrap { display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap; }
.form { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 22px 26px; width: 420px; }
.form h3 { margin: 0 0 16px; color: #2b5876; }
.form label { display: block; font-size: 13px; color: #555; margin-bottom: 12px; }
.form input, .form select { width: 100%; margin-top: 4px; padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 13px; box-sizing: border-box; }
.form button { width: 100%; padding: 10px; border: none; border-radius: 6px; background: linear-gradient(135deg, #2b5876, #4e4376); color: #fff; font-size: 14px; cursor: pointer; }
.form button:disabled { opacity: .6; }
.err { color: #c44e52; font-size: 12px; margin-top: 10px; }
.result { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 22px 26px; min-width: 280px; }
.result h3 { margin: 0 0 12px; color: #2b5876; }
.big { font-size: 34px; font-weight: 700; color: #c44e52; }
.band { margin-top: 8px; color: #666; font-size: 14px; }
.note { margin-top: 14px; color: #999; font-size: 12px; }
</style>
